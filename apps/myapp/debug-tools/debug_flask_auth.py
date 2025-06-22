#!/usr/bin/env python3
"""
Debug the Flask authentication flow step by step.
"""

import sqlite3
import hashlib
import base64

def check_werkzeug_password(password_hash, password):
    """Manual password check that mimics Werkzeug exactly."""
    if not password_hash or not password_hash.startswith('pbkdf2:sha256:'):
        print(f"❌ Invalid hash format: {password_hash[:50] if password_hash else 'None'}...")
        return False
    
    try:
        # Parse: pbkdf2:sha256:iterations$salt$hash
        parts = password_hash.split('$')
        if len(parts) != 3:
            print(f"❌ Hash has {len(parts)} parts, expected 3")
            return False
        
        iterations_part = password_hash.split(':')[2].split('$')[0]
        iterations = int(iterations_part)
        salt_b64 = parts[1]
        expected_hash_b64 = parts[2]
        
        print(f"🔍 Hash details:")
        print(f"   Iterations: {iterations}")
        print(f"   Salt (b64): {salt_b64}")
        print(f"   Expected hash (b64): {expected_hash_b64[:20]}...")
        
        # Decode salt and compute hash
        salt = base64.b64decode(salt_b64)
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        computed_hash_b64 = base64.b64encode(computed_hash).decode('ascii')
        
        print(f"   Computed hash (b64): {computed_hash_b64[:20]}...")
        print(f"   Hashes match: {computed_hash_b64 == expected_hash_b64}")
        
        return computed_hash_b64 == expected_hash_b64
    except Exception as e:
        print(f"❌ Password check error: {e}")
        return False

def simulate_flask_auth():
    """Simulate the exact Flask authentication flow."""
    print("=== SIMULATING FLASK AUTHENTICATION ===\n")
    
    # Step 1: Form data simulation
    username_or_email = "admin"
    password = "password"
    
    print(f"1. Form Data Received:")
    print(f"   username_or_email: '{username_or_email}'")
    print(f"   password: '{password}'")
    print()
    
    # Step 2: Database query (simulating User.authenticate)
    conn = sqlite3.connect('../instance/accessible_outings.db')
    cursor = conn.cursor()
    
    print(f"2. Database Query:")
    query = "SELECT * FROM users WHERE username = ? OR email = ?"
    print(f"   SQL: {query}")
    print(f"   Params: ('{username_or_email}', '{username_or_email}')")
    
    cursor.execute(query, (username_or_email, username_or_email))
    result = cursor.fetchone()
    
    if result:
        column_names = [description[0] for description in cursor.description]
        user_data = dict(zip(column_names, result))
        print(f"   ✅ User found: {user_data['username']}")
        print(f"   User ID: {user_data['id']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Is Admin: {user_data['is_admin']}")
        print()
        
        # Step 3: Password verification
        print(f"3. Password Verification:")
        password_hash = user_data['password_hash']
        print(f"   Stored hash: {password_hash[:50]}...")
        
        password_valid = check_werkzeug_password(password_hash, password)
        print(f"   Password valid: {password_valid}")
        print()
        
        if password_valid:
            print("🎉 AUTHENTICATION SHOULD SUCCEED")
            print(f"   User: {user_data['username']}")
            print(f"   Admin: {user_data['is_admin']}")
            
            # Step 4: Check potential Flask issues
            print("\n4. Potential Flask Issues to Check:")
            print("   - CSRF token validation")
            print("   - Session management")
            print("   - Login form field names")
            print("   - Flash message handling")
            print("   - Redirect logic")
            
        else:
            print("❌ AUTHENTICATION SHOULD FAIL - PASSWORD MISMATCH")
            
    else:
        print("   ❌ No user found")
        print("   This explains the 'invalid username/email' error")
        
        # Check if there are any users at all
        cursor.execute("SELECT username, email FROM users")
        all_users = cursor.fetchall()
        print(f"\n   All users in database:")
        for username, email in all_users:
            print(f"     - Username: '{username}', Email: '{email}'")
    
    conn.close()
    
    # Step 5: Form field debugging
    print(f"\n5. Form Field Debugging:")
    print(f"   Check that login form uses exactly these field names:")
    print(f"   - name='username_or_email' (current: should match)")
    print(f"   - name='password' (current: should match)")
    print(f"   - Make sure there are no extra spaces or hidden characters")

def debug_login_template():
    """Check the login template for potential issues."""
    print("\n=== LOGIN TEMPLATE DEBUGGING ===")
    
    with open('templates/auth/login.html', 'r') as f:
        content = f.read()
    
    # Check form field names
    if 'name="username_or_email"' in content:
        print("✅ username_or_email field found")
    else:
        print("❌ username_or_email field NOT found")
    
    if 'name="password"' in content:
        print("✅ password field found")
    else:
        print("❌ password field NOT found")
    
    # Check form method
    if 'method="POST"' in content:
        print("✅ POST method found")
    else:
        print("❌ POST method NOT found")

if __name__ == '__main__':
    simulate_flask_auth()
    debug_login_template()