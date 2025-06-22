#!/usr/bin/env python3
"""
Test the exact authentication flow that Flask is using.
"""

import sqlite3
import hashlib
import base64

class MockUser:
    """Mock user class that mimics the Flask User model."""
    def __init__(self, row_data, column_names):
        for i, col_name in enumerate(column_names):
            setattr(self, col_name, row_data[i])
    
    def check_password(self, password):
        """Check password using the same logic as Werkzeug."""
        return check_werkzeug_password(self.password_hash, password)

def check_werkzeug_password(password_hash, password):
    """Check password against Werkzeug hash - exact replica."""
    if not password_hash or not password_hash.startswith('pbkdf2:sha256:'):
        return False
    
    try:
        # Parse: pbkdf2:sha256:iterations$salt$hash
        parts = password_hash.split('$')
        if len(parts) != 3:
            return False
        
        iterations_part = password_hash.split(':')[2].split('$')[0]
        iterations = int(iterations_part)
        salt_b64 = parts[1]
        expected_hash_b64 = parts[2]
        
        # Decode salt and compute hash
        salt = base64.b64decode(salt_b64)
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        computed_hash_b64 = base64.b64encode(computed_hash).decode('ascii')
        
        return computed_hash_b64 == expected_hash_b64
    except Exception as e:
        print(f"Password check error: {e}")
        return False

def authenticate(username_or_email, password):
    """Exact replica of User.authenticate method."""
    conn = sqlite3.connect('instance/accessible_outings.db')
    cursor = conn.cursor()
    
    # This is the exact query from the User model
    query = """
    SELECT * FROM users 
    WHERE username = ? OR email = ?
    """
    
    cursor.execute(query, (username_or_email, username_or_email))
    result = cursor.fetchone()
    
    if result:
        column_names = [description[0] for description in cursor.description]
        user = MockUser(result, column_names)
        
        print(f"Found user: {user.username}")
        print(f"Password hash: {user.password_hash[:50]}...")
        
        # Test password
        password_match = user.check_password(password)
        print(f"Password match: {password_match}")
        
        if password_match:
            conn.close()
            return user
    else:
        print("No user found with that username/email")
    
    conn.close()
    return None

def test_authentication():
    """Test various authentication scenarios."""
    print("=== TESTING AUTHENTICATION ===")
    
    test_cases = [
        ("admin", "password"),
        ("admin@example.com", "password"),
        ("admin", "wrong"),
        ("ADMIN", "password"),
        ("admin ", "password"),  # with space
        (" admin", "password"),  # with space
    ]
    
    for username_or_email, password in test_cases:
        print(f"\nTesting: '{username_or_email}' / '{password}'")
        user = authenticate(username_or_email, password)
        if user:
            print(f"✅ SUCCESS: Authenticated as {user.username} (admin: {user.is_admin})")
        else:
            print("❌ FAILED: Authentication failed")

if __name__ == '__main__':
    test_authentication()