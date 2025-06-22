#!/usr/bin/env python3
"""
Clean up admin user and ensure single, correct setup.
"""

import sqlite3
import hashlib
import base64

def create_clean_admin():
    """Create a clean admin user with known working credentials."""
    
    # Create a simple, known-working password hash
    password = "password"
    salt = b'saltsalt12345678'  # Fixed salt for consistency
    iterations = 260000
    
    # Create PBKDF2 hash
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    
    # Encode as base64
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
    
    # Format as Werkzeug expects
    password_hash = f"pbkdf2:sha256:{iterations}${salt_b64}${hash_b64}"
    
    print(f"Generated password hash: {password_hash}")
    
    # Connect to database
    conn = sqlite3.connect('../instance/accessible_outings.db')
    cursor = conn.cursor()
    
    # Delete any existing admin users
    cursor.execute("DELETE FROM users WHERE username = 'admin'")
    print(f"Deleted {cursor.rowcount} existing admin users")
    
    # Create fresh admin user
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, created_at, updated_at)
        VALUES ('admin', 'admin@example.com', ?, 'Admin', 'User', 1, datetime('now'), datetime('now'))
    """, (password_hash,))
    
    conn.commit()
    
    # Verify the user was created
    cursor.execute("SELECT id, username, email, is_admin, password_hash FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        user_id, username, email, is_admin, stored_hash = result
        print(f"\n✅ Clean admin user created:")
        print(f"   ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Is Admin: {is_admin}")
        print(f"   Hash matches: {stored_hash == password_hash}")
        
        # Test the password
        def test_password(stored_hash, test_pass):
            parts = stored_hash.split('$')
            if len(parts) != 3:
                return False
            
            iterations = int(stored_hash.split(':')[2].split('$')[0])
            salt = base64.b64decode(parts[1])
            expected_hash = base64.b64decode(parts[2])
            
            test_hash = hashlib.pbkdf2_hmac('sha256', test_pass.encode('utf-8'), salt, iterations)
            return test_hash == expected_hash
        
        password_test = test_password(stored_hash, 'password')
        print(f"   Password test: {'✅ PASS' if password_test else '❌ FAIL'}")
        
    else:
        print("❌ Failed to create admin user")
    
    # Show all users
    cursor.execute("SELECT username, email, is_admin FROM users")
    users = cursor.fetchall()
    print(f"\nAll users in database:")
    for username, email, is_admin in users:
        admin_status = " (ADMIN)" if is_admin else ""
        print(f"  - {username} ({email}){admin_status}")
    
    conn.close()
    
    print("\n" + "="*50)
    print("CLEAN ADMIN SETUP COMPLETE")
    print("Username: admin")
    print("Password: password")
    print("="*50)

if __name__ == '__main__':
    create_clean_admin()