#!/usr/bin/env python3

"""
Test authentication using the actual Flask User model.
"""

import os
import sys
from flask import Flask
from config import get_config
from models import db
from models.user import User

def create_app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)
    
    db.init_app(app)
    return app

def test_authentication():
    """Test authentication using the Flask User model."""
    print("🧪 TESTING FLASK USER AUTHENTICATION")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found!")
            return
        
        print(f"👤 Testing user: {admin_user.username} (ID: {admin_user.id})")
        print(f"📧 Email: {admin_user.email}")
        print(f"🔐 Password hash: {admin_user.password_hash[:50]}...")
        
        test_cases = [
            ("admin", "password"),
            ("admin@example.com", "password"),
            ("admin", "wrong"),
            ("ADMIN", "password"),
        ]
        
        for username_or_email, password in test_cases:
            print(f"\n🔍 Testing: '{username_or_email}' / '{password}'")
            
            # Test 1: Direct password check
            if username_or_email.lower() in ['admin', 'admin@example.com']:
                direct_check = admin_user.check_password(password)
                print(f"   Direct check: {'✅ SUCCESS' if direct_check else '❌ FAILED'}")
            
            # Test 2: User.authenticate method
            try:
                auth_result = User.authenticate(username_or_email, password)
                if auth_result:
                    print(f"   Authenticate method: ✅ SUCCESS ({auth_result.username})")
                else:
                    print(f"   Authenticate method: ❌ FAILED")
            except Exception as e:
                print(f"   Authenticate method: 💥 ERROR - {e}")

if __name__ == '__main__':
    test_authentication()