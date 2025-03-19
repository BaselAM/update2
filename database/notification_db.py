import sqlite3
import os
import datetime
from pathlib import Path


class NotificationDatabase:
    """Database handler for storing and retrieving notifications"""

    def __init__(self, db_path=None):
        """Initialize the notification database"""
        if db_path is None:
            # Store in user's home directory by default
            home_dir = Path.home()
            app_data_dir = home_dir / '.car_parts_app'
            os.makedirs(app_data_dir, exist_ok=True)
            db_path = app_data_dir / 'notifications.db'

        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create the notifications table if it doesn't exist"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                importance INTEGER DEFAULT 1,
                category TEXT DEFAULT 'general'
            )
        ''')

        conn.commit()
        conn.close()

    def add_notification(self, title, message, category='general', importance=1):
        """Add a new notification to the database"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notifications (title, message, timestamp, importance, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, message, timestamp, importance, category))

        notification_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return notification_id

    def mark_as_read(self, notification_id):
        """Mark a notification as read"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE notifications
            SET read = 1
            WHERE id = ?
        ''', (notification_id,))

        conn.commit()
        conn.close()

    def mark_all_as_read(self):
        """Mark all notifications as read"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE notifications
            SET read = 1
        ''')

        conn.commit()
        conn.close()

    def get_unread_count(self):
        """Get the count of unread notifications"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM notifications
            WHERE read = 0
        ''')

        count = cursor.fetchone()[0]

        conn.close()

        return count

    def get_notifications(self, limit=50, include_read=False, category=None):
        """Get recent notifications with optional filtering"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = "SELECT id, title, message, timestamp, read, importance, category FROM notifications"
        conditions = []
        params = []

        if not include_read:
            conditions.append("read = 0")

        if category:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row[0],
                'title': row[1],
                'message': row[2],
                'time': self._format_time(row[3]),
                'timestamp': row[3],
                'read': bool(row[4]),
                'importance': row[5],
                'category': row[6]
            })

        conn.close()

        return notifications

    def delete_notification(self, notification_id):
        """Delete a notification by ID"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM notifications
            WHERE id = ?
        ''', (notification_id,))

        conn.commit()
        conn.close()

    def delete_all_read(self):
        """Delete all read notifications"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM notifications
            WHERE read = 1
        ''')

        conn.commit()
        conn.close()

    def _format_time(self, timestamp_str):
        """Format timestamp for display"""
        try:
            now = datetime.datetime.now()
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # If from today, show only time
            if timestamp.date() == now.date():
                return f"Today {timestamp.strftime('%H:%M')}"

            # If from yesterday
            yesterday = now.date() - datetime.timedelta(days=1)
            if timestamp.date() == yesterday:
                return f"Yesterday {timestamp.strftime('%H:%M')}"

            # If from this year
            if timestamp.year == now.year:
                return timestamp.strftime("%b %d, %H:%M")

            # Otherwise, full date
            return timestamp.strftime("%b %d, %Y")

        except (ValueError, TypeError):
            return timestamp_str  # Return as-is if parsing fails