#!/usr/bin/env python3
"""
Fix admin password using Flask app context.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_admin_password():
    """Fix admin password with proper Flask context."""
    try:
        from app import create_app
        from models import db
        from models.user import User
        
        app = create_app()
        
        with app.app_context():
            # Find admin user
            admin_user = User.query.filter_by(username='admin').first()
            
            if admin_user:
                print(f"Found admin user: {admin_user.username}")
                print(f"Current password hash: {admin_user.password_hash[:50]}...")
                
                # Set the password properly using the User model method
                admin_user.set_password('password')
                admin_user.is_admin = True  # Ensure admin status
                db.session.commit()
                
                print("Admin password updated successfully!")
                print("Username: admin")
                print("Password: password")
                
                # Test the authentication
                test_user = User.authenticate('admin', 'password')
                if test_user:
                    print("✅ Authentication test PASSED")
                else:
                    print("❌ Authentication test FAILED")
                    
            else:
                print("Admin user not found, creating new admin user...")
                admin_user = User.create_user(
                    username='admin',
                    email='admin@example.com',
                    password='password',
                    first_name='Admin',
                    last_name='User',
                    is_admin=True
                )
                print("✅ Admin user created successfully!")
                print("Username: admin")
                print("Password: password")
                
    except Exception as e:
        print(f"Flask method failed: {e}")
        # Fall back to direct database update
        try:
            import sqlite3
            from werkzeug.security import generate_password_hash
            
            password_hash = generate_password_hash('password')
            conn = sqlite3.connect('instance/accessible_outings.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (password_hash,))
            conn.commit()
            conn.close()
            print("✅ Admin password updated via direct database access")
            print("Username: admin")
            print("Password: password")
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")

if __name__ == '__main__':
    fix_admin_password()