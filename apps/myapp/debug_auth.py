#!/usr/bin/env python3
"""
Debug authentication issue by testing the exact authentication flow.
"""

import sqlite3
import hashlib
import base64

def check_werkzeug_password(password_hash, password):
    """
    Manually check password against Werkzeug hash format.
    This mimics what Werkzeug's check_password_hash does.
    """
    if not password_hash.startswith('pbkdf2:sha256:'):
        return False
    
    # Parse the hash format: pbkdf2:sha256:iterations$salt$hash
    parts = password_hash.split('$')
    if len(parts) != 3:
        return False
    
    iterations_part = password_hash.split(':')[2].split('$')[0]
    iterations = int(iterations_part)
    salt_b64 = parts[1]
    expected_hash_b64 = parts[2]
    
    # Decode salt
    salt = base64.b64decode(salt_b64)
    
    # Generate hash with same parameters
    test_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    test_hash_b64 = base64.b64encode(test_hash).decode('ascii')
    
    return test_hash_b64 == expected_hash_b64

def debug_authentication():
    """Debug the authentication issue."""
    conn = sqlite3.connect('instance/accessible_outings.db')
    cursor = conn.cursor()
    
    # Get admin user details
    cursor.execute("SELECT id, username, email, password_hash, is_admin FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        user_id, username, email, password_hash, is_admin = result
        print("=== ADMIN USER DEBUG ===")
        print(f"ID: {user_id}")
        print(f"Username: '{username}'")
        print(f"Email: '{email}'")
        print(f"Is Admin: {is_admin}")
        print(f"Password Hash: {password_hash}")
        print(f"Hash Length: {len(password_hash)}")
        
        # Test password manually
        test_password = "password"
        manual_check = check_werkzeug_password(password_hash, test_password)
        print(f"Manual password check: {manual_check}")
        
        # Also test with variations
        test_passwords = ["password", "admin", "Password", "ADMIN"]
        for pwd in test_passwords:
            result = check_werkzeug_password(password_hash, pwd)
            print(f"Testing '{pwd}': {result}")
        
        print("\n=== TESTING QUERY VARIATIONS ===")
        # Test different ways the authenticate method might query
        test_queries = [
            ("SELECT * FROM users WHERE username = 'admin'", None),
            ("SELECT * FROM users WHERE email = 'admin@example.com'", None),
            ("SELECT * FROM users WHERE username = 'admin' OR email = 'admin'", None),
            ("SELECT * FROM users WHERE LOWER(username) = 'admin'", None),
        ]
        
        for query, params in test_queries:
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchone()
                print(f"Query: {query}")
                print(f"Result: {'Found' if result else 'Not found'}")
                if result:
                    print(f"  Username: '{result[1]}'")
                print()
            except Exception as e:
                print(f"Query failed: {query} - {e}")
    
    else:
        print("❌ Admin user not found!")
    
    # List all users for comparison
    print("\n=== ALL USERS ===")
    cursor.execute("SELECT id, username, email, is_admin FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]}, Username: '{user[1]}', Email: '{user[2]}', Admin: {user[3]}")
    
    conn.close()

if __name__ == '__main__':
    debug_authentication()