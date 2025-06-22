#!/usr/bin/env python3
"""
Database Migration and Schema Update Module

This module ensures the database schema is up-to-date with the latest model definitions.
Run this when switching between development environments to synchronize schema changes.

Usage:
    python db_migration.py
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_db_path():
    """Get the database file path."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, '..', 'instance', 'accessible_outings.db')

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def apply_user_schema_updates(cursor):
    """Apply schema updates to the users table."""
    print("Checking users table schema...")
    
    # Add is_admin column if missing
    if not check_column_exists(cursor, 'users', 'is_admin'):
        print("  Adding is_admin column...")
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
        print("  ✓ Added is_admin column")
    else:
        print("  ✓ is_admin column already exists")

def apply_venue_schema_updates(cursor):
    """Apply schema updates to the venues table."""
    print("Checking venues table schema...")
    
    # Columns to add with their definitions
    venue_columns = [
        ('experience_tags', 'TEXT'),
        ('interestingness_score', 'DECIMAL(3,2) DEFAULT 0.0'),
        ('event_frequency_score', 'INTEGER DEFAULT 0')
    ]
    
    for col_name, col_type in venue_columns:
        if not check_column_exists(cursor, 'venues', col_name):
            print(f"  Adding {col_name} column...")
            cursor.execute(f'ALTER TABLE venues ADD COLUMN {col_name} {col_type}')
            print(f"  ✓ Added {col_name} column")
        else:
            print(f"  ✓ {col_name} column already exists")

def create_events_tables(cursor):
    """Create events-related tables if they don't exist."""
    print("Creating events tables...")
    
    # Check if events table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    if not cursor.fetchone():
        print("  Creating events table...")
        cursor.execute('''
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            venue_id INTEGER NOT NULL REFERENCES venues(id),
            start_date DATE NOT NULL,
            start_time TIME,
            end_date DATE,
            end_time TIME,
            duration_hours REAL,
            is_fun BOOLEAN DEFAULT 0,
            is_interesting BOOLEAN DEFAULT 0,
            is_off_beat BOOLEAN DEFAULT 0,
            cost VARCHAR(100),
            registration_required BOOLEAN DEFAULT 0,
            registration_url VARCHAR(500),
            contact_phone VARCHAR(20),
            contact_email VARCHAR(120),
            max_participants INTEGER,
            age_restriction VARCHAR(50),
            audience_type VARCHAR(100),
            wheelchair_accessible BOOLEAN DEFAULT 0,
            hearing_accessible BOOLEAN DEFAULT 0,
            vision_accessible BOOLEAN DEFAULT 0,
            mobility_accommodations TEXT,
            accessibility_notes TEXT,
            indoor_outdoor VARCHAR(20),
            weather_dependent BOOLEAN DEFAULT 0,
            bring_items TEXT,
            provided_items TEXT,
            experience_tags TEXT,
            fun_score DECIMAL(3,2) DEFAULT 0.0,
            learning_potential DECIMAL(3,2) DEFAULT 0.0,
            uniqueness_score DECIMAL(3,2) DEFAULT 0.0,
            event_url VARCHAR(500),
            image_url VARCHAR(500),
            social_media_links TEXT,
            source VARCHAR(100),
            external_id VARCHAR(255),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_recurring BOOLEAN DEFAULT 0,
            recurrence_pattern VARCHAR(100)
        )
        ''')
        print("  ✓ Created events table")
    else:
        print("  ✓ Events table already exists")
    
    # Check if event_favorites table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_favorites'")
    if not cursor.fetchone():
        print("  Creating event_favorites table...")
        cursor.execute('''
        CREATE TABLE event_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            event_id INTEGER NOT NULL REFERENCES events(id),
            notes TEXT,
            reminder_set BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, event_id)
        )
        ''')
        print("  ✓ Created event_favorites table")
    else:
        print("  ✓ Event_favorites table already exists")
    
    # Check if event_reviews table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_reviews'")
    if not cursor.fetchone():
        print("  Creating event_reviews table...")
        cursor.execute('''
        CREATE TABLE event_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            event_id INTEGER NOT NULL REFERENCES events(id),
            attended BOOLEAN DEFAULT 1,
            overall_rating INTEGER,
            accessibility_rating INTEGER,
            fun_rating INTEGER,
            review_text TEXT,
            accessibility_notes TEXT,
            would_attend_again BOOLEAN,
            would_recommend BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("  ✓ Created event_reviews table")
    else:
        print("  ✓ Event_reviews table already exists")
    
    # Create indexes for events
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date)",
        "CREATE INDEX IF NOT EXISTS idx_events_venue_id ON events(venue_id)",
        "CREATE INDEX IF NOT EXISTS idx_events_is_fun ON events(is_fun)",
        "CREATE INDEX IF NOT EXISTS idx_events_is_interesting ON events(is_interesting)",
        "CREATE INDEX IF NOT EXISTS idx_events_is_off_beat ON events(is_off_beat)",
        "CREATE INDEX IF NOT EXISTS idx_events_wheelchair_accessible ON events(wheelchair_accessible)",
        "CREATE INDEX IF NOT EXISTS idx_event_favorites_user_id ON event_favorites(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_event_reviews_event_id ON event_reviews(event_id)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    print("  ✓ Created event indexes")

def enable_admin_for_username(cursor):
    """Enable admin features for the 'admin' username account."""
    print("Configuring admin access...")
    
    # Check if admin user exists
    cursor.execute("SELECT id, is_admin FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        user_id, is_admin = admin_user
        if not is_admin:
            print("  Enabling admin privileges for 'admin' user...")
            cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
            print("  ✓ Admin privileges enabled for 'admin' user")
        else:
            print("  ✓ 'admin' user already has admin privileges")
    else:
        print("  ℹ 'admin' user does not exist yet - admin privileges will be enabled when account is created")

def create_admin_trigger(cursor):
    """Create trigger to automatically enable admin for 'admin' username."""
    print("Setting up admin trigger...")
    
    # Drop existing trigger if it exists
    cursor.execute("DROP TRIGGER IF EXISTS auto_enable_admin")
    
    # Create trigger to automatically enable admin for 'admin' username
    trigger_sql = """
    CREATE TRIGGER auto_enable_admin 
        AFTER INSERT ON users
        FOR EACH ROW
        WHEN NEW.username = 'admin'
        BEGIN
            UPDATE users SET is_admin = 1 WHERE id = NEW.id;
        END;
    """
    
    cursor.execute(trigger_sql)
    print("  ✓ Auto-admin trigger created for 'admin' username")

def verify_schema(cursor):
    """Verify that all expected columns exist."""
    print("Verifying schema integrity...")
    
    expected_user_columns = ['id', 'username', 'email', 'password_hash', 'first_name', 
                           'last_name', 'home_zip_code', 'max_travel_minutes', 
                           'accessibility_needs', 'is_admin', 'created_at', 'updated_at']
    
    expected_venue_columns = ['id', 'google_place_id', 'name', 'address', 'city', 'state',
                            'zip_code', 'phone', 'website', 'latitude', 'longitude',
                            'category_id', 'google_rating', 'price_level', 'wheelchair_accessible',
                            'accessible_parking', 'accessible_restroom', 'elevator_access',
                            'wide_doorways', 'ramp_access', 'accessible_seating',
                            'accessibility_notes', 'hours_monday', 'hours_tuesday',
                            'hours_wednesday', 'hours_thursday', 'hours_friday',
                            'hours_saturday', 'hours_sunday', 'seasonal_hours',
                            'experience_tags', 'interestingness_score', 'event_frequency_score',
                            'last_updated', 'created_at', 'verified_accessible', 'photo_urls']
    
    # Check users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    missing_user_cols = set(expected_user_columns) - set(user_columns)
    
    if missing_user_cols:
        print(f"  ⚠ Missing user columns: {missing_user_cols}")
        return False
    else:
        print("  ✓ Users table schema is complete")
    
    # Check venues table
    cursor.execute("PRAGMA table_info(venues)")
    venue_columns = [row[1] for row in cursor.fetchall()]
    missing_venue_cols = set(expected_venue_columns) - set(venue_columns)
    
    if missing_venue_cols:
        print(f"  ⚠ Missing venue columns: {missing_venue_cols}")
        return False
    else:
        print("  ✓ Venues table schema is complete")
    
    return True

def run_migration():
    """Run the complete database migration."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        print("Please ensure the application has been initialized and the database created.")
        return False
    
    print(f"Starting database migration for: {db_path}")
    print(f"Migration started at: {datetime.now()}")
    print("-" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Apply schema updates
        apply_user_schema_updates(cursor)
        apply_venue_schema_updates(cursor)
        create_events_tables(cursor)
        
        # Configure admin access
        enable_admin_for_username(cursor)
        create_admin_trigger(cursor)
        
        # Commit all changes
        conn.commit()
        
        # Verify schema
        schema_valid = verify_schema(cursor)
        
        conn.close()
        
        print("-" * 50)
        if schema_valid:
            print("✅ Database migration completed successfully!")
            print("All schema updates have been applied and verified.")
        else:
            print("⚠ Migration completed with warnings - some columns may be missing")
        
        print(f"Migration finished at: {datetime.now()}")
        return schema_valid
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_current_schema():
    """Display current database schema for debugging."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Current Database Schema:")
        print("=" * 50)
        
        # Show users table schema
        print("\nUSERS TABLE:")
        cursor.execute("PRAGMA table_info(users)")
        for row in cursor.fetchall():
            print(f"  {row[1]} ({row[2]})")
        
        # Show venues table schema
        print("\nVENUES TABLE:")
        cursor.execute("PRAGMA table_info(venues)")
        for row in cursor.fetchall():
            print(f"  {row[1]} ({row[2]})")
        
        # Show admin users
        print("\nADMIN USERS:")
        cursor.execute("SELECT username, is_admin FROM users WHERE is_admin = 1")
        admin_users = cursor.fetchall()
        if admin_users:
            for username, is_admin in admin_users:
                print(f"  {username} (admin: {bool(is_admin)})")
        else:
            print("  No admin users found")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show-schema":
        show_current_schema()
    else:
        success = run_migration()
        if not success:
            sys.exit(1)