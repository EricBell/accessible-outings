#!/usr/bin/env python3
"""
User Manager - Admin tool for managing user accounts
Features:
1. Verify username/password combinations
2. Change user passwords
3. Delete user accounts
4. List all users
"""
import sys
import os
import sqlite3
import getpass
from werkzeug.security import check_password_hash, generate_password_hash

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class UserManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'accessible_outings.db')
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found at {self.db_path}")
            sys.exit(1)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def verify_credentials(self, username, password):
        """Verify username and password combination"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Try to find user by username or email
            cursor.execute("""
                SELECT id, username, email, password_hash, is_admin, created_at
                FROM users 
                WHERE username = ? OR email = ?
            """, (username, username))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return {
                    'success': False,
                    'message': f"❌ User '{username}' not found",
                    'user_info': None
                }
            
            user_id, db_username, email, password_hash, is_admin, created_at = user
            
            # Verify password
            if check_password_hash(password_hash, password):
                return {
                    'success': True,
                    'message': f"✅ Credentials verified successfully for '{db_username}'",
                    'user_info': {
                        'id': user_id,
                        'username': db_username,
                        'email': email,
                        'is_admin': bool(is_admin),
                        'created_at': created_at,
                        'last_login': 'Not tracked'
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f"❌ Invalid password for user '{db_username}'",
                    'user_info': {
                        'id': user_id,
                        'username': db_username,
                        'email': email,
                        'is_admin': bool(is_admin)
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Database error: {e}",
                'user_info': None
            }
    
    def change_password(self, username, new_password):
        """Change password for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Find user
            cursor.execute("""
                SELECT id, username, email
                FROM users 
                WHERE username = ? OR email = ?
            """, (username, username))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {
                    'success': False,
                    'message': f"❌ User '{username}' not found"
                }
            
            user_id, db_username, email = user
            
            # Generate new password hash
            new_password_hash = generate_password_hash(new_password)
            
            # Update password
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?
                WHERE id = ?
            """, (new_password_hash, user_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f"✅ Password updated successfully for user '{db_username}' (ID: {user_id})"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Error updating password: {e}"
            }
    
    def delete_user(self, username):
        """Delete a user account"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Find user first
            cursor.execute("""
                SELECT id, username, email, is_admin
                FROM users 
                WHERE username = ? OR email = ?
            """, (username, username))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {
                    'success': False,
                    'message': f"❌ User '{username}' not found"
                }
            
            user_id, db_username, email, is_admin = user
            
            # Safety check - don't delete admin users without confirmation
            if is_admin:
                confirm = input(f"⚠️  WARNING: '{db_username}' is an admin user. Delete anyway? (type 'DELETE' to confirm): ")
                if confirm != 'DELETE':
                    conn.close()
                    return {
                        'success': False,
                        'message': "❌ Deletion cancelled - admin user protection"
                    }
            
            # Delete related data first (foreign key constraints)
            cursor.execute("DELETE FROM user_favorites WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_reviews WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM event_favorites WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM event_reviews WHERE user_id = ?", (user_id,))
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f"✅ User '{db_username}' (ID: {user_id}) deleted successfully along with all related data"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Error deleting user: {e}"
            }
    
    def list_users(self):
        """List all users in the system"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, is_admin, created_at
                FROM users 
                ORDER BY is_admin DESC, username ASC
            """)
            
            users = cursor.fetchall()
            conn.close()
            
            return {
                'success': True,
                'users': users,
                'message': f"Found {len(users)} users"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Error listing users: {e}",
                'users': []
            }

def print_user_info(user_info):
    """Print formatted user information"""
    if not user_info:
        return
    
    print(f"\n📋 User Information:")
    print(f"   ID: {user_info['id']}")
    print(f"   Username: {user_info['username']}")
    print(f"   Email: {user_info['email']}")
    print(f"   Admin: {'Yes' if user_info['is_admin'] else 'No'}")
    print(f"   Created: {user_info.get('created_at', 'Unknown')}")
    print(f"   Last Login: {user_info.get('last_login', 'Never')}")

def main():
    """Main interactive menu"""
    manager = UserManager()
    
    print("👤 User Manager - Admin Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Verify user credentials")
        print("2. Change user password")
        print("3. Delete user account")
        print("4. List all users")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            # Verify credentials
            print("\n🔍 Verify User Credentials")
            print("-" * 30)
            username = input("Username or email: ").strip()
            if not username:
                print("❌ Username cannot be empty")
                continue
            
            password = getpass.getpass("Password: ")
            
            result = manager.verify_credentials(username, password)
            print(f"\n{result['message']}")
            
            if result['user_info']:
                print_user_info(result['user_info'])
        
        elif choice == '2':
            # Change password
            print("\n🔐 Change User Password")
            print("-" * 30)
            username = input("Username or email: ").strip()
            if not username:
                print("❌ Username cannot be empty")
                continue
            
            # First verify user exists
            verify_result = manager.verify_credentials(username, "dummy_password")
            if not verify_result['user_info']:
                print(f"❌ User '{username}' not found")
                continue
            
            print(f"Found user: {verify_result['user_info']['username']}")
            
            new_password = getpass.getpass("New password: ")
            if len(new_password) < 6:
                print("❌ Password must be at least 6 characters")
                continue
            
            confirm_password = getpass.getpass("Confirm new password: ")
            if new_password != confirm_password:
                print("❌ Passwords don't match")
                continue
            
            result = manager.change_password(username, new_password)
            print(f"\n{result['message']}")
        
        elif choice == '3':
            # Delete user
            print("\n🗑️  Delete User Account")
            print("-" * 30)
            username = input("Username or email to delete: ").strip()
            if not username:
                print("❌ Username cannot be empty")
                continue
            
            # Show user info first
            verify_result = manager.verify_credentials(username, "dummy_password")
            if not verify_result['user_info']:
                print(f"❌ User '{username}' not found")
                continue
            
            print_user_info(verify_result['user_info'])
            
            confirm = input(f"\n⚠️  Are you sure you want to delete '{verify_result['user_info']['username']}'? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Deletion cancelled")
                continue
            
            result = manager.delete_user(username)
            print(f"\n{result['message']}")
        
        elif choice == '4':
            # List users
            print("\n👥 All Users")
            print("-" * 30)
            result = manager.list_users()
            
            if result['success']:
                print(f"\n{result['message']}\n")
                
                if result['users']:
                    print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Admin':<6} {'Created':<20}")
                    print("-" * 85)
                    
                    for user in result['users']:
                        user_id, username, email, is_admin, created_at = user
                        admin_str = "Yes" if is_admin else "No"
                        created_str = created_at[:19] if created_at else "Unknown"
                        
                        print(f"{user_id:<4} {username:<20} {email:<30} {admin_str:<6} {created_str:<20}")
                else:
                    print("No users found")
            else:
                print(result['message'])
        
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-5.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)