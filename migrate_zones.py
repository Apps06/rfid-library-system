import sqlite3
import os

db_path = os.path.join('instance', 'library.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE attendance_logs ADD COLUMN zone VARCHAR(50) DEFAULT 'Library';")
        conn.commit()
        print("Successfully added 'zone' column to attendance_logs table.")
    except sqlite3.OperationalError as e:
        print(f"Column already exists or error: {e}")
    finally:
        conn.close()
else:
    print("Database file not found.")
