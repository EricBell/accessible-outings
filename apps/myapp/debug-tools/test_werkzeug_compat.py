#!/usr/bin/env python3
"""
Test if our password hash is compatible with Werkzeug's check_password_hash.
"""

import sqlite3

def test_werkzeug_compatibility():
    """Test if Werkzeug can check our password hash."""
    try:
        from werkzeug.security import check_password_hash
        
        # Get the admin user's password hash
        conn = sqlite3.connect('instance/accessible_outings.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            password_hash = result[0]
            print(f"Password hash: {password_hash}")
            
            # Test with Werkzeug's check_password_hash
            test_password = "password"
            result = check_password_hash(password_hash, test_password)
            print(f"Werkzeug check_password_hash result: {result}")
            
            if result:
                print("✅ Password hash is compatible with Werkzeug!")
            else:
                print("❌ Password hash is NOT compatible with Werkzeug!")
                
                # Try creating a new hash with Werkzeug
                from werkzeug.security import generate_password_hash
                new_hash = generate_password_hash(test_password)
                print(f"New Werkzeug hash: {new_hash}")
                
                # Update database with Werkzeug-generated hash
                conn = sqlite3.connect('instance/accessible_outings.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (new_hash,))
                conn.commit()
                conn.close()
                print("✅ Updated admin password with proper Werkzeug hash")
        else:
            print("❌ Admin user not found!")
            
    except ImportError:
        print("❌ Werkzeug not available in this environment")

if __name__ == '__main__':
    test_werkzeug_compatibility()