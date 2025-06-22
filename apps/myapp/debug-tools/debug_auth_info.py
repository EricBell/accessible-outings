#!/usr/bin/env python3
"""
Show Flask debug information when authentication fails.
"""

import sqlite3
import os

def show_debug_info():
    """Show comprehensive debug information."""
    print("🔍 FLASK AUTHENTICATION DEBUG INFO")
    print("=" * 50)
    
    # Check database
    print("\n📊 DATABASE STATUS:")
    if os.path.exists('../instance/accessible_outings.db'):
        conn = sqlite3.connect('../instance/accessible_outings.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   Total users: {user_count}")
        
        cursor.execute("SELECT username, email, is_admin FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        if admin:
            print(f"   Admin user: {admin[0]} ({admin[1]}) - Admin: {admin[2]}")
        else:
            print("   ❌ No admin user found")
        
        conn.close()
    else:
        print("   ❌ Database file not found")
    
    # Check configuration
    print("\n⚙️ CONFIGURATION:")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
        
        if 'BYPASS_AUTH=False' in env_content:
            print("   ✅ BYPASS_AUTH is False")
        else:
            print("   ⚠️ BYPASS_AUTH setting unclear")
    else:
        print("   ❌ .env file not found")
    
    # Check templates
    print("\n📄 TEMPLATES:")
    if os.path.exists('templates/auth/login.html'):
        with open('templates/auth/login.html', 'r') as f:
            login_content = f.read()
        
        if 'name="username_or_email"' in login_content:
            print("   ✅ Username field found")
        else:
            print("   ❌ Username field missing")
        
        if 'name="password"' in login_content:
            print("   ✅ Password field found")
        else:
            print("   ❌ Password field missing")
        
        if 'method="POST"' in login_content:
            print("   ✅ POST method found")
        else:
            print("   ❌ POST method missing")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Restart Flask application")
    print("2. Try login with admin/password")
    print("3. Check Flask console for debug messages")
    print("4. Look for messages starting with 🔍, 👤, 🔐, ✅, ❌")

if __name__ == '__main__':
    show_debug_info()
