#!/usr/bin/env python3
"""
Test authentication within Flask app context to identify issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_flask_auth():
    """Test authentication within proper Flask context."""
    try:
        from app import create_app
        from models import db
        from models.user import User
        
        app = create_app()
        
        with app.app_context():
            print("=== TESTING FLASK AUTHENTICATION CONTEXT ===")
            
            # Test 1: Database connection
            print("\n1. Database Connection Test:")
            try:
                user_count = User.query.count()
                print(f"   ✅ Database connected - {user_count} users found")
            except Exception as e:
                print(f"   ❌ Database error: {e}")
                return
            
            # Test 2: Find admin user
            print("\n2. Admin User Lookup:")
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f"   ✅ Admin user found: {admin_user.username}")
                print(f"   Email: {admin_user.email}")
                print(f"   Is Admin: {admin_user.is_admin}")
                print(f"   Password hash: {admin_user.password_hash[:50]}...")
            else:
                print("   ❌ Admin user not found")
                return
            
            # Test 3: Authentication method
            print("\n3. Authentication Test:")
            test_user = User.authenticate('admin', 'password')
            if test_user:
                print(f"   ✅ Authentication successful: {test_user.username}")
                print(f"   Full name: {test_user.full_name}")
                print(f"   Admin status: {test_user.is_admin}")
            else:
                print("   ❌ Authentication failed")
            
            # Test 4: Alternative lookups
            print("\n4. Alternative Lookup Tests:")
            by_email = User.authenticate('admin@example.com', 'password')
            print(f"   By email: {'✅ Success' if by_email else '❌ Failed'}")
            
            by_username_wrong_pass = User.authenticate('admin', 'wrongpass')
            print(f"   Wrong password: {'❌ Should fail' if not by_username_wrong_pass else '✅ Unexpected success'}")
            
            # Test 5: Check password method directly
            print("\n5. Direct Password Check:")
            password_valid = admin_user.check_password('password')
            print(f"   Password check result: {password_valid}")
            
            if password_valid:
                print("\n🎉 ALL TESTS PASSED - Authentication should work in Flask!")
            else:
                print("\n❌ PASSWORD CHECK FAILED - This is the issue!")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Flask environment not available for testing")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    test_flask_auth()