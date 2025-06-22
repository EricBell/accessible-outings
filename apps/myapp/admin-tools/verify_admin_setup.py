#!/usr/bin/env python3
"""
Verify admin user setup using SQLite directly.
"""

import sqlite3
import os

def verify_admin_setup():
    """Check admin user configuration."""
    db_path = 'instance/accessible_outings.db'
    
    if not os.path.exists(db_path):
        print("Database does not exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if admin user exists
    cursor.execute("SELECT id, username, email, is_admin, password_hash FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        user_id, username, email, is_admin, password_hash = result
        print(f"Admin user found:")
        print(f"  ID: {user_id}")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Is Admin: {is_admin}")
        print(f"  Has Password Hash: {'Yes' if password_hash else 'No'}")
        print(f"  Password Hash Length: {len(password_hash) if password_hash else 0}")
        
        # Try to set a simple password hash if none exists
        if not password_hash:
            # Simple hash for testing - should be replaced with proper Werkzeug hash
            simple_hash = "pbkdf2:sha256:260000$test$password_hash_placeholder"
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (simple_hash,))
            conn.commit()
            print("  -> Added placeholder password hash")
    else:
        print("Admin user not found!")
        
        # Create admin user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, created_at, last_updated)
            VALUES ('admin', 'admin@example.com', 'pbkdf2:sha256:260000$test$placeholder', 'Admin', 'User', 1, datetime('now'), datetime('now'))
        """)
        conn.commit()
        print("Created admin user with placeholder password")
    
    # List all users
    cursor.execute("SELECT username, email, is_admin FROM users")
    users = cursor.fetchall()
    print(f"\nAll users in database:")
    for username, email, is_admin in users:
        admin_status = " (ADMIN)" if is_admin else ""
        print(f"  - {username} ({email}){admin_status}")
    
    conn.close()

if __name__ == '__main__':
    verify_admin_setup()