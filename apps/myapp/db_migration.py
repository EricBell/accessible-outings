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
    return os.path.join(base_dir, 'instance', 'accessible_outings.db')

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