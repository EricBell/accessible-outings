#!/usr/bin/env python3

"""
Final Admin Password Fix

This script will reset the admin password to 'password' and verify it works.
"""

import os
import sys
from flask import Flask
from config import get_config
from models import db
from models.user import User

def create_app():
    """Create Flask app for admin password fix."""
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)
    
    db.init_app(app)
    return app

def fix_admin_password():
    """Fix the admin password once and for all."""
    print("🔧 FIXING ADMIN PASSWORD")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # Find admin user
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        print(f"👤 Found admin user: {admin_user.username} (ID: {admin_user.id})")
        print(f"📧 Email: {admin_user.email}")
        print(f"🔐 Current password hash: {admin_user.password_hash[:50]}...")
        
        # Set new password
        print("\n🔄 Setting new password to 'password'...")
        admin_user.set_password('password')
        
        # Save to database
        try:
            db.session.commit()
            print("✅ Password updated and saved to database")
        except Exception as e:
            print(f"❌ Failed to save password: {e}")
            db.session.rollback()
            return False
        
        # Test the new password immediately
        print("\n🧪 Testing new password...")
        
        # Test direct password check
        if admin_user.check_password('password'):
            print("✅ Direct password check: SUCCESS")
        else:
            print("❌ Direct password check: FAILED")
            return False
        
        # Test authenticate method
        auth_result = User.authenticate('admin', 'password')
        if auth_result:
            print(f"✅ User.authenticate: SUCCESS ({auth_result.username})")
        else:
            print("❌ User.authenticate: FAILED")
            return False
        
        # Test with email
        auth_result_email = User.authenticate('admin@example.com', 'password')
        if auth_result_email:
            print(f"✅ Email authenticate: SUCCESS ({auth_result_email.username})")
        else:
            print("❌ Email authenticate: FAILED")
            return False
        
        print(f"\n🔐 New password hash: {admin_user.password_hash[:50]}...")
        
        return True

def test_other_passwords():
    """Test what other passwords might work."""
    print("\n🔍 TESTING OTHER POSSIBLE PASSWORDS")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        
        # Common passwords that might have been set
        test_passwords = [
            'admin',
            'password123',
            'admin123',
            'Password',
            'PASSWORD',
            '123456',
            'secret',
            'admin_password',
            '',  # empty password
        ]
        
        print("Testing common passwords...")
        for pwd in test_passwords:
            if admin_user.check_password(pwd):
                print(f"✅ FOUND WORKING PASSWORD: '{pwd}'")
                return pwd
            else:
                print(f"❌ Failed: '{pwd}'")
        
        return None

def main():
    """Main function."""
    print("🔧 ADMIN PASSWORD DIAGNOSTIC AND FIX")
    print("=" * 60)
    
    # First, test if there's a password that works
    working_password = test_other_passwords()
    
    if working_password:
        print(f"\n🎉 Found working password: '{working_password}'")
        print("No need to reset password.")
        return
    
    # If no password works, reset it
    print("\n💡 No working password found. Resetting to 'password'...")
    
    if fix_admin_password():
        print("\n🎉 SUCCESS! Admin password has been reset.")
        print("\n📋 LOGIN CREDENTIALS:")
        print("   Username: admin")
        print("   Password: password")
        print("\n   OR")
        print("\n   Email: admin@example.com")
        print("   Password: password")
        print("\n🚀 You can now login to the application!")
    else:
        print("\n💥 FAILED to fix admin password. Check the errors above.")

if __name__ == '__main__':
    main()