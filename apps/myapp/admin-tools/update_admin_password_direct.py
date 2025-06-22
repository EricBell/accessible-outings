#!/usr/bin/env python3
"""
Direct password update for admin user using proper Werkzeug format.
"""

import sqlite3
from werkzeug.security import generate_password_hash

def update_admin_password():
    """Update admin password with proper Werkzeug hashing."""
    # Generate proper password hash
    password_hash = generate_password_hash('password')
    
    # Update database
    conn = sqlite3.connect('instance/accessible_outings.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (password_hash,))
    conn.commit()
    
    # Verify update
    cursor.execute("SELECT username, is_admin FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        print(f"Admin password updated successfully!")
        print(f"Username: {result[0]}")
        print(f"Admin status: {result[1]}")
        print("Password: password")
    else:
        print("Admin user not found!")
    
    conn.close()

if __name__ == '__main__':
    try:
        update_admin_password()
    except ImportError:
        print("Werkzeug not available. Password may not work properly.")