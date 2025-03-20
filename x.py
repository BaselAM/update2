import sqlite3
import os
from pathlib import Path
import datetime


def initialize_all_products():
    """Loads ALL product names from btw_filenames.txt into car_parts.db"""
    # Get file paths
    project_dir = Path(__file__).resolve().parent
    db_path = project_dir / "database" / "car_parts.db"
    resource_path = project_dir / "resources" / "btw_filenames.txt"

    print(f"Database path: {db_path}")
    print(f"Resource path: {resource_path}")

    # Check if the resource file exists
    if not os.path.exists(resource_path):
        print(f"Error: Resource file not found: {resource_path}")
        return False

    # Make sure the database directory exists
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created database directory: {db_dir}")

    # Use current date as the timestamp
    current_timestamp = "2025-03-19 23:49:07"  # Updated timestamp

    try:
        # Read ALL product names from the file
        product_names = []
        with open(resource_path, 'r', encoding='utf-8') as f:
            for line in f:
                name = line.strip()
                if name:  # Skip empty lines
                    product_names.append(name)

        if not product_names:
            print("Error: No product names found in the file.")
            return False

        print(f"Found {len(product_names)} product names in {resource_path}")

        # Connect to the database (create it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
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
        ''')

        # Commit the table creation (end any implicit transaction)
        conn.commit()

        # Start a new transaction explicitly
        conn.isolation_level = None  # This allows us to control transactions manually
        cursor.execute("BEGIN")

        # Delete existing products if any
        cursor.execute("DELETE FROM parts")
        print("Cleared existing products from database")

        # Insert ALL product names
        count = 0
        for name in product_names:
            cursor.execute("""
                INSERT INTO parts 
                (category, car_name, model, product_name, quantity, price, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("3", "-", "-", name, 0, 0.0, current_timestamp))
            count += 1

            # Provide progress updates
            if count % 100 == 0:
                print(f"Inserted {count} products...")

        # Commit the transaction
        cursor.execute("COMMIT")
        print(f"Successfully inserted {count} products into database")

        # Verify the number of records
        cursor.execute("SELECT COUNT(*) FROM parts")
        db_count = cursor.fetchone()[0]
        print(f"Database now contains {db_count} products")

        # Close the connection
        conn.close()

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
        # Try to rollback the transaction if an error occurs
        try:
            if conn and cursor:
                cursor.execute("ROLLBACK")
                print("Transaction rolled back due to error")
        except:
            pass
        return False


if __name__ == "__main__":
    print(f"Starting database initialization as user: BaselAM")
    print(f"Current timestamp: 2025-03-19 23:49:07")

    success = initialize_all_products()

    if success:
        print("Database initialization completed successfully!")
    else:
        print("Database initialization failed!")