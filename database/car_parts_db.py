import sqlite3
from pathlib import Path
import threading
import logging


class CarPartsDB:
    """Thread-safe database handler for car parts inventory"""

    def __init__(self, db_path=None):
        # Configure logging
        self.logger = logging.getLogger('CarPartsDB')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # If no db_path provided, default to the 'database' folder inside the project root
        if db_path is None:
            # This assumes your project structure: Project/database/car_parts.db
            self.db_path = Path(
                __file__).resolve().parent.parent / "database/car_parts.db"
        else:
            self.db_path = Path(db_path)

        # Thread-local storage for connections
        self.local = threading.local()
        self.lock = threading.RLock()  # Reentrant lock for thread safety

        # Initialize main thread connection
        self.connect()
        self.logger.info(f"Initialized database connection to {self.db_path}")

    def connect(self):
        """Create a thread-local database connection"""
        try:
            # Close existing connection for this thread if it exists
            self.close_local_connection()

            # Create new connection for this thread
            self.local.conn = sqlite3.connect(self.db_path, timeout=10.0)
            self.local.conn.execute("PRAGMA foreign_keys = ON")
            self.local.cursor = self.local.conn.cursor()

            # Create table if needed
            self.create_table()

            thread_id = threading.get_ident()
            self.logger.info(f"Thread {thread_id}: Database connection established")

        except sqlite3.Error as e:
            self.logger.error(f"Connection error: {str(e)}")
            raise

    def create_table(self):
        """Create table if it doesn't exist"""
        query = '''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            car_name TEXT NOT NULL,
            model TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            price REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.execute_query(query)

    def close_local_connection(self):
        """Close the connection for the current thread"""
        if hasattr(self.local, 'cursor') and self.local.cursor:
            try:
                self.local.cursor.close()
            except Exception as e:
                self.logger.warning(f"Error closing cursor: {e}")
            self.local.cursor = None

        if hasattr(self.local, 'conn') and self.local.conn:
            try:
                self.local.conn.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")
            self.local.conn = None

    def close_connection(self):
        """Close all connections - for shutdown"""
        self.close_local_connection()

    def ensure_connection(self):
        """Ensure this thread has a valid connection"""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.connect()

    def execute_query(self, query, params=()):
        """Execute a query with the thread-local connection"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.cursor.execute(query, params)
                return self.local.cursor
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    self.create_table()
                    self.local.cursor.execute(query, params)
                    return self.local.cursor
                else:
                    self.logger.error(f"Database error: {e}")
                    # Try reconnecting
                    self.connect()
                    self.local.cursor.execute(query, params)
                    return self.local.cursor
            except sqlite3.Error as e:
                self.logger.error(f"SQL error: {e}")
                raise

    def add_part(self, category, car_name, model, product_name, quantity, price):
        """Add a new part with explicit verification"""
        with self.lock:
            self.ensure_connection()
            try:
                # Validate inputs and provide defaults for required fields
                if not product_name or product_name.strip() == "":
                    self.logger.error("Cannot add part: product name is required")
                    return False

                # Set defaults for required fields that can't be NULL
                category = category if category and category.strip() else "3"  # Use default category "3"
                car_name = car_name if car_name and car_name.strip() else "-"  # Use default "-"
                model = model if model and model.strip() else "-"  # Use default "-"

                # Convert and validate numeric values
                try:
                    quantity = int(quantity) if quantity is not None else 0
                    price = float(price) if price is not None else 0.0
                except (ValueError, TypeError):
                    self.logger.error("Invalid quantity or price values")
                    quantity = 0
                    price = 0.0

                thread_id = threading.get_ident()
                self.logger.info(f"Thread {thread_id}: Adding part: '{product_name}'")

                # Use explicit transaction
                self.local.conn.execute("BEGIN TRANSACTION")

                self.local.cursor.execute("""
                    INSERT INTO parts 
                    (category, car_name, model, product_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (category, car_name, model, product_name, quantity, price))

                # Get the ID of the inserted row
                new_id = self.local.cursor.lastrowid
                self.logger.info(f"Created new part with ID: {new_id}")

                # Explicitly commit the transaction
                self.local.conn.commit()

                # Verify the part was added by trying to fetch it
                self.local.cursor.execute("SELECT * FROM parts WHERE id = ?", (new_id,))
                result = self.local.cursor.fetchone()

                if result:
                    self.logger.info(
                        f"Successfully verified part was added with ID: {new_id}")
                    return True
                else:
                    self.logger.error(
                        f"Failed to verify part was added with ID: {new_id}")
                    return False

            except sqlite3.Error as e:
                self.logger.error(f"Database error in add_part: {e}")
                # Try to rollback if there was an error
                try:
                    self.local.conn.rollback()
                except:
                    pass
                return False

    def sync_database(self):
        """Force database to write changes to disk"""
        with self.lock:
            self.ensure_connection()
            try:
                # Execute PRAGMA to force a write to disk
                self.local.cursor.execute("PRAGMA wal_checkpoint")

                # Execute a simple query to verify database is functioning
                self.local.cursor.execute("SELECT COUNT(*) FROM parts")
                count = self.local.cursor.fetchone()[0]

                thread_id = threading.get_ident()
                self.logger.info(
                    f"Thread {thread_id}: Database synced and verified with {count} parts")
                return True
            except sqlite3.Error as e:
                self.logger.error(f"Error syncing database: {e}")
                return False

    def count_parts(self):
        """Count total number of parts in database - basic health check"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.cursor.execute("SELECT COUNT(*) FROM parts")
                return self.local.cursor.fetchone()[0]
            except sqlite3.Error as e:
                self.logger.error(f"Error counting parts: {e}")
                return 0

    def get_part(self, part_id):
        """Get a single part by ID"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.cursor.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
                return self.local.cursor.fetchone()
            except sqlite3.Error as e:
                self.logger.error(f"Error fetching part {part_id}: {e}")
                return None

    def get_all_parts(self):
        """Get all parts ordered by last updated"""
        with self.lock:
            self.ensure_connection()
            try:
                thread_id = threading.get_ident()
                self.logger.info(f"Thread {thread_id}: Fetching all parts")
                self.local.cursor.execute(
                    "SELECT * FROM parts ORDER BY last_updated DESC")
                return self.local.cursor.fetchall()
            except sqlite3.Error as e:
                self.logger.error(f"Error fetching all parts: {e}")
                return []

    def update_part(self, part_id, **kwargs):
        """Update a part with detailed audit logging"""
        with self.lock:
            self.ensure_connection()
            try:
                # First, get the original part data for comparison
                self.local.cursor.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
                original_part = self.local.cursor.fetchone()

                if not original_part:
                    self.logger.warning(
                        f"Attempted to update non-existent part #{part_id}")
                    return False

                # Build the update query
                set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
                set_clause += ", last_updated = CURRENT_TIMESTAMP"  # Always update timestamp
                values = list(kwargs.values()) + [part_id]

                # Execute the update
                self.local.cursor.execute(f"""
                    UPDATE parts 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                self.local.conn.commit()

                # Check if update was successful
                if self.local.cursor.rowcount > 0:
                    # Log what specifically changed
                    thread_id = threading.get_ident()
                    changes = []

                    # Get column names for reference
                    self.local.cursor.execute("PRAGMA table_info(parts)")
                    columns = {row[0]: row[1] for row in self.local.cursor.fetchall()}

                    # Compare and log each changed field
                    for key in kwargs:
                        col_idx = None
                        # Find the column index for this field
                        for idx, name in columns.items():
                            if name == key:
                                col_idx = idx
                                break

                        if col_idx is not None and col_idx < len(original_part):
                            old_value = original_part[col_idx]
                            new_value = kwargs[key]

                            if str(old_value) != str(new_value):
                                # Use ASCII-compatible characters instead of Unicode arrow
                                changes.append(f"{key}: '{old_value}' -> '{new_value}'")

                    # Log the changes
                    if changes:
                        changes_str = ", ".join(changes)
                        self.logger.info(
                            f"Thread {thread_id}: Updated part #{part_id} - {changes_str}")
                    else:
                        self.logger.info(
                            f"Thread {thread_id}: Updated part #{part_id} - no changes detected")

                    return True
                else:
                    self.logger.warning(f"Update part #{part_id} - no rows affected")
                    return False

            except sqlite3.Error as e:
                self.logger.error(f"Database error updating part #{part_id}: {e}")
                return False

    def delete_part(self, part_id):
        """Delete a part by ID"""
        with self.lock:
            self.ensure_connection()
            try:
                thread_id = threading.get_ident()
                self.logger.info(f"Thread {thread_id}: Deleting part {part_id}")
                self.local.cursor.execute("DELETE FROM parts WHERE id = ?", (part_id,))
                self.local.conn.commit()
                return self.local.cursor.rowcount > 0
            except sqlite3.Error as e:
                self.logger.error(f"Database error: {str(e)}")
                return False

    def delete_multiple_parts(self, part_ids):
        """Delete multiple parts in a single transaction"""
        if not part_ids:
            self.logger.warning("No part IDs provided for deletion")
            return False

        with self.lock:
            self.ensure_connection()
            try:
                # Start transaction
                self.begin_transaction()

                # Delete parts in batches to avoid parameter limit
                batch_size = 100
                deleted_count = 0

                for i in range(0, len(part_ids), batch_size):
                    batch = part_ids[i:i + batch_size]
                    placeholders = ','.join(['?'] * len(batch))

                    self.local.cursor.execute(
                        f"DELETE FROM parts WHERE id IN ({placeholders})",
                        batch
                    )
                    deleted_count += self.local.cursor.rowcount

                self.commit_transaction()
                thread_id = threading.get_ident()
                self.logger.info(
                    f"Thread {thread_id}: Deleted {deleted_count} parts in batch operation")
                return deleted_count > 0

            except sqlite3.Error as e:
                # Roll back on error
                self.rollback_transaction()
                self.logger.error(f"Error during batch deletion: {e}")
                return False

    def search_parts(self, search_term=''):
        """Search parts by any field"""
        with self.lock:
            self.ensure_connection()
            query = '''
            SELECT * FROM parts 
            WHERE car_name LIKE ? 
               OR model LIKE ? 
               OR product_name LIKE ?
            '''
            try:
                self.local.cursor.execute(
                    query,
                    (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
                )
                return self.local.cursor.fetchall()
            except sqlite3.Error as e:
                self.logger.error(f"Search error: {e}")
                return []

    def get_part_by_name(self, product_name):
        """Fetch part by product name"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.cursor.execute(
                    "SELECT * FROM parts WHERE product_name = ?",
                    (product_name,)
                )
                return self.local.cursor.fetchone()
            except sqlite3.Error as e:
                self.logger.error(f"Error getting part by name: {e}")
                return None

    def search_products_starting_with(self, search_text, limit=5):
        """Return product names starting with search text"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.cursor.execute("""
                    SELECT product_name FROM parts
                    WHERE product_name LIKE ? COLLATE NOCASE
                    ORDER BY product_name
                    LIMIT ?
                """, (f"{search_text}%", limit))
                return [row[0] for row in self.local.cursor.fetchall()]
            except Exception as e:
                self.logger.error(f"Search error: {e}")
                return []

    def get_unique_cars(self):
        """Get list of unique car names - added since error indicates this is missing"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.cursor.execute(
                    "SELECT DISTINCT car_name FROM parts WHERE car_name != '-' ORDER BY car_name"
                )
                return [row[0] for row in self.local.cursor.fetchall()]
            except sqlite3.Error as e:
                self.logger.error(f"Error getting unique cars: {e}")
                return []

    def begin_transaction(self):
        """Begin a transaction in the current thread's connection"""
        with self.lock:
            self.ensure_connection()
            try:
                self.local.conn.execute("BEGIN TRANSACTION")
                thread_id = threading.get_ident()
                self.logger.info(f"Thread {thread_id}: Transaction started")
                return True
            except sqlite3.Error as e:
                self.logger.error(f"Error starting transaction: {e}")
                return False

    def commit_transaction(self):
        """Commit the current transaction"""
        with self.lock:
            if hasattr(self.local, 'conn') and self.local.conn:
                try:
                    self.local.conn.commit()
                    thread_id = threading.get_ident()
                    self.logger.info(f"Thread {thread_id}: Transaction committed")
                    return True
                except sqlite3.Error as e:
                    self.logger.error(f"Error committing transaction: {e}")
                    return False
            return False

    def rollback_transaction(self):
        """Roll back the current transaction"""
        with self.lock:
            if hasattr(self.local, 'conn') and self.local.conn:
                try:
                    self.local.conn.rollback()
                    thread_id = threading.get_ident()
                    self.logger.info(f"Thread {thread_id}: Transaction rolled back")
                    return True
                except sqlite3.Error as e:
                    self.logger.error(f"Error rolling back transaction: {e}")
                    return False
            return False

