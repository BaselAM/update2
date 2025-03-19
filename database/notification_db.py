import sqlite3
from datetime import datetime, timedelta
import os
from pathlib import Path


class NotificationDatabaseConnector:
    """Connector for handling notification database operations"""

    def __init__(self, db_path=None):
        """Initialize the database connector with optional custom path"""
        if db_path is None:
            # Default path in the application directory
            app_dir = Path(__file__).resolve().parent.parent
            db_path = os.path.join(app_dir, 'data', 'notifications.db')

            # Ensure data directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._create_tables_if_not_exist()

    def _create_tables_if_not_exist(self):
        """Create notification tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            priority TEXT DEFAULT 'normal',
            category TEXT,
            is_read INTEGER DEFAULT 0,
            user_id TEXT
        )
        ''')

        # Create user preferences table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            user_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            sound_enabled INTEGER DEFAULT 1,
            display_time INTEGER DEFAULT 5
        )
        ''')

        conn.commit()
        conn.close()

    def get_notifications_for_user(self, user_id, limit=20, include_read=False):
        """Get recent notifications for a specific user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        query = "SELECT * FROM notifications WHERE user_id = ?"
        params = [user_id]

        if not include_read:
            query += " AND is_read = 0"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_unread_notification_count(self, user_id):
        """Get the count of unread notifications for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def mark_notification_as_read(self, notification_id, user_id=None):
        """Mark a specific notification as read"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "UPDATE notifications SET is_read = 1 WHERE id = ?"
        params = [notification_id]

        # Add user check for security if provided
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        cursor.execute(query, params)
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def mark_all_as_read(self, user_id):
        """Mark all notifications for a user as read"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()

    def add_notification(self, user_id, title, message, category=None, priority='normal'):
        """Add a new notification for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO notifications (user_id, title, message, category, priority) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, message, category, priority)
        )

        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return notification_id

    def add_sample_notifications(self, user_id):
        """Add some sample notifications for testing"""
        # Clear existing sample notifications for this user
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
        conn.commit()

        # Sample notifications with different timestamps
        now = datetime.now()
        samples = [
            (user_id, "New Products", "5 new brake pads added to inventory", "inventory",
             "normal", now),
            (user_id, "Low Stock Alert", "Oil filters (ACME #F100) are low", "inventory",
             "high", now - timedelta(hours=5)),
            (user_id, "System Update", "Maintenance tonight at 11 PM", "system", "normal",
             now - timedelta(days=1)),
            (user_id, "Payment Received", "Customer #1432 payment processed", "sales",
             "normal", now - timedelta(days=2)),
            (user_id, "New Feature Available", "Check out the new reporting system",
             "system", "normal", now - timedelta(days=3)),
        ]

        cursor.executemany(
            "INSERT INTO notifications (user_id, title, message, category, priority, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            samples
        )
        conn.commit()
        conn.close()