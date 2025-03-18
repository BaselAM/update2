import sqlite3
from pathlib import Path
import threading
class CarPartsDB:
    """Handles database operations for car parts inventory"""

    def __init__(self, db_path=None):
        self.lock = threading.Lock()
        # If no db_path provided, default to the 'database' folder inside the project root
        if db_path is None:
            # This assumes your project structure: Project/database/car_parts.db
            self.db_path = Path(__file__).resolve().parent.parent / "database/car_parts.db"
        else:
            self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None
        self.connect()  # This calls create_table()

    def create_table(self):
        """Correct schema with last_updated column"""
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

    def execute_query(self, query, params=()):
        with self.lock:
            try:
                if not self.conn:
                    self.connect()
                self.cursor.execute(query, params)
                return self.cursor
            except sqlite3.OperationalError:
                self.connect()  # Reconnect if needed
                self.cursor.execute(query, params)
                return self.cursor

    def add_part(self, category, car_name, model, product_name, quantity, price):
        try:
            if not self.conn:
                self.connect()
            self.cursor.execute("""
                INSERT INTO parts 
                (category, car_name, model, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (category, car_name, model, product_name, quantity, price))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def search_parts(self, search_term=''):
        """Search parts by any field"""
        query = '''
        SELECT * FROM parts 
        WHERE car_name LIKE ? 
           OR model LIKE ? 
           OR product_name LIKE ?
        '''
        return self.execute_query(
            query,
            (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
        ).fetchall()

    def get_part(self, part_id):
        """Get a single part by ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
            return cursor.fetchone()
        finally:
            if conn:
                conn.close()

    def get_all_parts(self):
        """Get all parts ordered by last updated"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parts ORDER BY last_updated DESC")
            return cursor.fetchall()
        finally:
            conn.close()

    def update_part(self, part_id, **kwargs):
        try:
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [part_id]
            self.cursor.execute(f"""
                UPDATE parts 
                SET {set_clause}
                WHERE id = ?
            """, values)
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def delete_part(self, part_id):
        """Delete a part by ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM parts WHERE id = ?", (part_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_multiple_parts(self, part_ids):
        """Safe method to delete multiple parts"""
        try:
            placeholders = ','.join(['?'] * len(part_ids))
            self.cursor.execute(
                f"DELETE FROM parts WHERE id IN ({placeholders})",
                part_ids
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def search_products_starting_with(self, search_text, limit=5):
        """Return product names starting with search text (case-insensitive)"""
        try:
            self.cursor.execute("""
                SELECT product_name FROM parts
                WHERE product_name LIKE ? COLLATE NOCASE
                ORDER BY product_name
                LIMIT ?
            """, (f"{search_text}%", limit))
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def close_connection(self):
        """Safely close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.conn = None
        self.cursor = None

    def get_part_by_name(self, product_name):
        """Fetch part by product name"""
        query = 'SELECT * FROM parts WHERE product_name = ?'
        return self.execute_query(query, (product_name,)).fetchone()

    def connect(self):
        """Establish and maintain connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.conn.cursor()
            self.create_table()
        except sqlite3.Error as e:
            print(f"Connection error: {str(e)}")
            raise

    def get_connection(self):
        """Create new connection for each operation"""
        return sqlite3.connect(self.db_path)

if __name__ == "__main__":
    # Create an instance of the database
    db = CarPartsDB()

    script_dir = Path(__file__).parent.absolute()
    file_path = script_dir / 'resources' / 'btw_filenames.txt'  # Adjusted path for resources directory

    # Only populate if empty
    if not db.get_all_parts():
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                product_names = [line.strip() for line in file if line.strip()]
                for name in product_names:
                    db.add_part(
                        category="-",
                        car_name="-",
                        model="-",
                        product_name=name,
                        quantity=0,
                        price=0.00
                    )
                print(f"Inserted {len(product_names)} products from file")
        except FileNotFoundError:
            print(f"Error: {file_path} not found!")
        except Exception as e:
            print(f"Database initialization error: {str(e)}")

    # Always show database contents
    print("\nCurrent database contents:")
    parts = db.get_all_parts()
    for part in parts:
        print(part)
    db.close_connection()
