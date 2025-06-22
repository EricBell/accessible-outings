#!/usr/bin/env python3
"""
Add debugging to the User authenticate method.
"""

def add_debug_to_user_model():
    """Add debugging to the User model authenticate method."""
    
    # Read the current user.py file
    with open('models/user.py', 'r') as f:
        content = f.read()
    
    # Replace the authenticate method with a debugging version
    old_authenticate = '''    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate a user by username/email and password."""
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            return user
        return None'''
    
    new_authenticate = '''    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate a user by username/email and password."""
        print(f"[DEBUG] Authenticating: '{username_or_email}' / '{password}'")
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        print(f"[DEBUG] User found: {user.username if user else 'None'}")
        
        if user:
            print(f"[DEBUG] Password hash: {user.password_hash[:50]}...")
            password_check = user.check_password(password)
            print(f"[DEBUG] Password check result: {password_check}")
            
            if password_check:
                print(f"[DEBUG] Authentication SUCCESS for {user.username}")
                return user
            else:
                print(f"[DEBUG] Authentication FAILED - wrong password")
        else:
            print(f"[DEBUG] Authentication FAILED - user not found")
        
        return None'''
    
    if old_authenticate in content:
        content = content.replace(old_authenticate, new_authenticate)
        
        # Write back
        with open('models/user.py', 'w') as f:
            f.write(content)
        
        print("✅ Added debugging to User.authenticate method")
        print("Now when you run the Flask app, you'll see debug output in the console")
    else:
        print("❌ Could not find the authenticate method to replace")

if __name__ == '__main__':
    add_debug_to_user_model()