#!/usr/bin/env python3
"""
Script to create admin user and add admin column to database.
"""

import sqlite3
import os
import hashlib

def simple_hash_password(password):
    """Simple password hashing (for development only)."""
    # Using a simple hash for now - in production you'd use proper bcrypt/scrypt
    return hashlib.sha256(f"salt{password}".encode()).hexdigest()

def add_admin_column_and_user():
    """Add admin column to users table and create admin user."""
    db_path = 'instance/accessible_outings.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add is_admin column if it doesn't exist
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        print("Added is_admin column to users table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("is_admin column already exists")
        else:
            print(f"Error adding is_admin column: {e}")
    
    # Check if admin user already exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        # Update existing admin user to have admin privileges
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
        print("Updated existing admin user with admin privileges")
    else:
        # Create new admin user with proper Werkzeug hash format
        # This mimics what Werkzeug generates: method$salt$hash
        password_hash = 'pbkdf2:sha256:600000$salt$' + simple_hash_password('password')
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, ('admin', 'admin@example.com', password_hash, 'Admin', 'User', 1))
        print("Created new admin user (username: admin, password: password)")
    
    conn.commit()
    
    # Verify admin user
    cursor.execute("SELECT username, email, is_admin FROM users WHERE username = 'admin'")
    admin_info = cursor.fetchone()
    if admin_info:
        print(f"Admin user verified: {admin_info[0]} ({admin_info[1]}) - Admin: {admin_info[2]}")
    
    conn.close()
    print("Admin setup completed successfully!")
    print("Note: You may need to update the password using the Flask app for proper Werkzeug hashing.")

if __name__ == '__main__':
    add_admin_column_and_user()