#!/usr/bin/env python3

"""
Comprehensive Login Flow Debug Script

This script will test every step of the login process to identify exactly where it's failing.
"""

import os
import sys
from flask import Flask
from config import get_config
from models import db
from models.user import User

def create_debug_app():
    """Create a minimal Flask app for debugging."""
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Force debug mode
    app.config['DEBUG'] = True
    
    # Initialize database
    db.init_app(app)
    
    return app

def test_user_model():
    """Test the User model directly."""
    print("=" * 60)
    print("🧪 TESTING USER MODEL DIRECTLY")
    print("=" * 60)
    
    app = create_debug_app()
    
    with app.app_context():
        # Test 1: Check if admin user exists
        print("\n1️⃣ Checking if admin user exists...")
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"   ✅ Admin user found: {admin_user.username} (ID: {admin_user.id})")
            print(f"   📧 Email: {admin_user.email}")
            print(f"   🔐 Password hash: {admin_user.password_hash[:50]}...")
            print(f"   👑 Is admin: {admin_user.is_admin}")
        else:
            print("   ❌ Admin user NOT found!")
            return False
        
        # Test 2: Test password checking directly
        print("\n2️⃣ Testing password validation directly...")
        test_passwords = ['password', 'admin', 'Password', 'PASSWORD']
        
        for pwd in test_passwords:
            result = admin_user.check_password(pwd)
            print(f"   Password '{pwd}': {'✅ VALID' if result else '❌ INVALID'}")
        
        # Test 3: Test authenticate method
        print("\n3️⃣ Testing User.authenticate method...")
        test_credentials = [
            ('admin', 'password'),
            ('admin@example.com', 'password'),
            ('ADMIN', 'password'),
            ('admin', 'wrong'),
        ]
        
        for username, password in test_credentials:
            print(f"\n   Testing: '{username}' / '{password}'")
            try:
                result = User.authenticate(username, password)
                if result:
                    print(f"   ✅ SUCCESS: {result.username} (Admin: {result.is_admin})")
                else:
                    print(f"   ❌ FAILED: No user returned")
            except Exception as e:
                print(f"   💥 ERROR: {e}")
        
        return True

def test_flask_login_flow():
    """Test the actual Flask login route."""
    print("=" * 60)
    print("🌐 TESTING FLASK LOGIN ROUTE")
    print("=" * 60)
    
    app = create_debug_app()
    
    # Register routes
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    with app.test_client() as client:
        with app.app_context():
            print("\n1️⃣ Testing GET request to login page...")
            response = client.get('/auth/login')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Login page loads successfully")
            else:
                print(f"   ❌ Login page failed: {response.status_code}")
                return False
            
            print("\n2️⃣ Testing POST request with admin credentials...")
            
            # Test data
            form_data = {
                'username_or_email': 'admin',
                'password': 'password'
            }
            
            print(f"   Sending form data: {form_data}")
            
            # Make POST request
            response = client.post('/auth/login', data=form_data, follow_redirects=False)
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 302:
                print(f"   ✅ Redirect received: {response.location}")
                print("   This suggests successful login!")
            elif response.status_code == 200:
                print("   ❌ No redirect - login likely failed")
                # Try to get the response content for error messages
                content = response.get_data(as_text=True)
                if "Invalid username" in content:
                    print("   💭 Found 'Invalid username' in response")
                if "error" in content.lower():
                    print("   💭 Found 'error' in response content")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
            
            return response.status_code == 302

def test_form_field_names():
    """Test if form field names match what the route expects."""
    print("=" * 60)
    print("📝 TESTING FORM FIELD NAMES")
    print("=" * 60)
    
    # Read the login template
    try:
        with open('templates/auth/login.html', 'r') as f:
            content = f.read()
        
        print("\n1️⃣ Checking form field names in template...")
        
        # Check for expected field names
        expected_fields = ['username_or_email', 'password', 'remember_me']
        
        for field in expected_fields:
            if f'name="{field}"' in content:
                print(f"   ✅ Found field: {field}")
            else:
                print(f"   ❌ Missing field: {field}")
        
        # Check form method
        if 'method="POST"' in content or "method='POST'" in content:
            print("   ✅ Form uses POST method")
        else:
            print("   ❌ Form does not use POST method")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading template: {e}")
        return False

def check_bypass_auth():
    """Check if BYPASS_AUTH is interfering."""
    print("=" * 60)
    print("⚙️ CHECKING BYPASS_AUTH CONFIGURATION")
    print("=" * 60)
    
    app = create_debug_app()
    
    with app.app_context():
        bypass_auth = app.config.get('BYPASS_AUTH', False)
        default_user_id = app.config.get('DEFAULT_USER_ID', 1)
        
        print(f"\n   BYPASS_AUTH: {bypass_auth}")
        print(f"   DEFAULT_USER_ID: {default_user_id}")
        
        if bypass_auth:
            print("   ⚠️  BYPASS_AUTH is enabled - this might interfere with login")
            
            # Check if default user exists
            default_user = User.query.get(default_user_id)
            if default_user:
                print(f"   Default user found: {default_user.username}")
            else:
                print(f"   ❌ Default user (ID: {default_user_id}) not found")
        else:
            print("   ✅ BYPASS_AUTH is disabled - normal authentication expected")

def main():
    """Run all debug tests."""
    print("🔍 COMPREHENSIVE LOGIN DEBUG")
    print("=" * 60)
    
    # Test 1: User model
    if not test_user_model():
        print("\n💥 User model test failed - stopping here")
        return
    
    # Test 2: Form field names
    test_form_field_names()
    
    # Test 3: BYPASS_AUTH check
    check_bypass_auth()
    
    # Test 4: Flask login flow
    test_flask_login_flow()
    
    print("\n" + "=" * 60)
    print("🏁 DEBUG COMPLETE")
    print("=" * 60)
    print("\n💡 If authentication is still failing:")
    print("   1. Check the Flask console output when you try to login")
    print("   2. Look for debug messages with 🔍, 👤, 🔐, ✅, ❌")
    print("   3. Make sure you restarted the Flask application")
    print("   4. Try using both 'admin' and 'admin@example.com' as username")

if __name__ == '__main__':
    main()