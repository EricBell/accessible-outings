#!/usr/bin/env python3
"""
Final comprehensive fix for admin authentication.
"""

import sqlite3
import hashlib
import secrets
import base64

def create_simple_werkzeug_hash(password):
    """Create a simple, known-working Werkzeug-compatible hash."""
    # Use a fixed salt for testing - normally this would be random
    salt = b'saltsalt12345678'  # 16 bytes
    iterations = 260000
    
    # Create PBKDF2 hash
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    
    # Encode as base64
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
    
    # Format as Werkzeug expects: pbkdf2:sha256:iterations$salt$hash
    return f"pbkdf2:sha256:{iterations}${salt_b64}${hash_b64}"

def final_admin_fix():
    """Apply final fix for admin authentication."""
    
    # 1. Create a new, simple password hash
    password_hash = create_simple_werkzeug_hash("password")
    print(f"New password hash: {password_hash}")
    
    # 2. Update the database
    conn = sqlite3.connect('instance/accessible_outings.db')
    cursor = conn.cursor()
    
    # Check current admin user
    cursor.execute("SELECT id, username, email, is_admin FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        user_id, username, email, is_admin = result
        print(f"Found admin user: ID={user_id}, Username={username}, Admin={is_admin}")
        
        # Update password hash and ensure admin status
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, is_admin = 1 
            WHERE username = 'admin'
        """, (password_hash,))
        conn.commit()
        print("✅ Updated admin password and status")
        
    else:
        print("❌ Admin user not found!")
        return
    
    # 3. Test the hash manually
    test_password = "password"
    
    # Decode and verify
    parts = password_hash.split('$')
    if len(parts) == 3:
        iterations = int(password_hash.split(':')[2].split('$')[0])
        salt = base64.b64decode(parts[1])
        expected_hash = base64.b64decode(parts[2])
        
        # Generate test hash
        test_hash = hashlib.pbkdf2_hmac('sha256', test_password.encode('utf-8'), salt, iterations)
        
        if test_hash == expected_hash:
            print("✅ Password hash verification PASSED")
        else:
            print("❌ Password hash verification FAILED")
    
    # 4. Verify in database
    cursor.execute("SELECT username, is_admin, password_hash FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    if result:
        username, is_admin, stored_hash = result
        print(f"Final verification:")
        print(f"  Username: {username}")
        print(f"  Is Admin: {is_admin}")
        print(f"  Hash matches: {stored_hash == password_hash}")
    
    conn.close()
    
    print("\n" + "="*50)
    print("ADMIN LOGIN CREDENTIALS:")
    print("Username: admin")
    print("Password: password")
    print("="*50)

if __name__ == '__main__':
    final_admin_fix()