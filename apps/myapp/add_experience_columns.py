#!/usr/bin/env python3
"""
Add experience columns to the existing database.
"""

import sqlite3
import os

def add_experience_columns():
    """Add new experience-related columns to the venues table."""
    db_path = 'instance/accessible_outings.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add experience_tags column (JSON array)
        cursor.execute("ALTER TABLE venues ADD COLUMN experience_tags TEXT DEFAULT '[]'")
        print("Added experience_tags column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("experience_tags column already exists")
        else:
            print(f"Error adding experience_tags: {e}")
    
    try:
        # Add interestingness_score column
        cursor.execute("ALTER TABLE venues ADD COLUMN interestingness_score REAL DEFAULT 0.0")
        print("Added interestingness_score column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("interestingness_score column already exists")
        else:
            print(f"Error adding interestingness_score: {e}")
    
    try:
        # Add event_frequency_score column
        cursor.execute("ALTER TABLE venues ADD COLUMN event_frequency_score INTEGER DEFAULT 0")
        print("Added event_frequency_score column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("event_frequency_score column already exists")
        else:
            print(f"Error adding event_frequency_score: {e}")
    
    try:
        # Add last_activity_update column
        cursor.execute("ALTER TABLE venues ADD COLUMN last_activity_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("Added last_activity_update column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("last_activity_update column already exists")
        else:
            print(f"Error adding last_activity_update: {e}")
    
    conn.commit()
    conn.close()
    print("Database schema updated successfully!")

if __name__ == '__main__':
    add_experience_columns()