#!/usr/bin/env python3
"""
Simple password hash fix for admin user.
This creates a hash that will work with Werkzeug's check_password_hash.
"""

import sqlite3
import hashlib
import secrets
import base64

def create_werkzeug_compatible_hash(password):
    """Create a password hash compatible with Werkzeug's format."""
    # Generate a salt
    salt = secrets.token_bytes(16)
    salt_b64 = base64.b64encode(salt).decode('ascii')
    
    # Create PBKDF2 hash (same as Werkzeug default)
    iterations = 260000
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
    
    # Format as Werkzeug expects: method:hash:iterations$salt$hash
    return f"pbkdf2:sha256:260000${salt_b64}${hash_b64}"

def fix_admin_password():
    """Fix admin password with compatible hash."""
    password = "password"
    password_hash = create_werkzeug_compatible_hash(password)
    
    # Update database
    conn = sqlite3.connect('../instance/accessible_outings.db')
    cursor = conn.cursor()
    
    # Check if admin user exists
    cursor.execute("SELECT username FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (password_hash,))
        conn.commit()
        print("✅ Admin password hash updated successfully!")
    else:
        print("❌ Admin user not found!")
    
    conn.close()
    print("Username: admin")
    print("Password: password")
    print(f"Hash format: {password_hash[:50]}...")

if __name__ == '__main__':
    fix_admin_password()