#!/usr/bin/env python3
"""
Enable comprehensive Flask debugging to identify authentication issues.
"""

def enable_flask_debugging():
    """Add detailed debugging to Flask routes and User model."""
    
    # 1. Add debugging to User model
    with open('models/user.py', 'r') as f:
        user_content = f.read()
    
    # Replace authenticate method with debug version
    debug_authenticate = '''    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate a user by username/email and password."""
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔍 User.authenticate called with: '{username_or_email}' / '{password}'")
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        logger.debug(f"👤 User found: {user.username if user else 'None'}")
        
        if user:
            logger.debug(f"🔐 Checking password for user: {user.username}")
            logger.debug(f"🗂️ Password hash: {user.password_hash[:50]}...")
            
            password_valid = user.check_password(password)
            logger.debug(f"✅ Password valid: {password_valid}")
            
            if password_valid:
                logger.debug(f"🎉 Authentication SUCCESS for {user.username}")
                return user
            else:
                logger.debug(f"❌ Authentication FAILED - password mismatch")
        else:
            logger.debug(f"❌ Authentication FAILED - user not found")
        
        return None'''
    
    # Replace the existing authenticate method
    start_marker = "    @staticmethod\n    def authenticate(username_or_email, password):"
    end_marker = "        return None"
    
    start_pos = user_content.find(start_marker)
    if start_pos != -1:
        # Find the end of the method
        lines = user_content[start_pos:].split('\n')
        method_lines = []
        indent_level = None
        
        for i, line in enumerate(lines):
            if i == 0:  # First line
                method_lines.append(line)
                continue
                
            # Determine indent level from second line
            if indent_level is None and line.strip():
                indent_level = len(line) - len(line.lstrip())
            
            # If we hit a line with same or less indentation (and it's not empty), we're done
            if line.strip() and indent_level is not None:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= 4:  # Back to class level
                    break
            
            method_lines.append(line)
        
        # Replace the method
        old_method = '\n'.join(method_lines)
        new_content = user_content.replace(old_method, debug_authenticate)
        
        with open('models/user.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Added debugging to User.authenticate method")
    else:
        print("❌ Could not find authenticate method in user.py")
    
    # 2. Add debugging to auth route
    with open('routes/auth.py', 'r') as f:
        auth_content = f.read()
    
    # Add logging import if not present
    if "import logging" not in auth_content:
        auth_content = auth_content.replace(
            "from flask import Blueprint",
            "import logging\nfrom flask import Blueprint"
        )
    
    # Add debug logging to login route
    debug_login_start = '''    if request.method == 'POST':
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.debug("🚀 Login POST request received")
        logger.debug(f"📝 Form data: {dict(request.form)}")
        logger.debug(f"🌐 Request headers: {dict(request.headers)}")
        
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        logger.debug(f"📋 Extracted - username_or_email: '{username_or_email}', password: '{password}'")
        
        if not username_or_email or not password:
            logger.debug(f"❌ Missing credentials - username_or_email: {bool(username_or_email)}, password: {bool(password)}")
            flash('Please provide both username/email and password.', 'error')
            return render_template('auth/login.html')
        
        logger.debug(f"🔑 Calling User.authenticate...")
        user = User.authenticate(username_or_email, password)
        logger.debug(f"👤 Authentication result: {user.username if user else 'None'}")'''
    
    # Replace the existing POST handling
    old_post_start = "    if request.method == 'POST':\n        username_or_email = request.form.get('username_or_email')"
    
    if old_post_start in auth_content:
        # Find the end of the POST block
        post_start = auth_content.find(old_post_start)
        remaining = auth_content[post_start:]
        lines = remaining.split('\n')
        
        post_lines = []
        for i, line in enumerate(lines):
            post_lines.append(line)
            if "user = User.authenticate(username_or_email, password)" in line:
                break
        
        old_post_block = '\n'.join(post_lines)
        new_auth_content = auth_content.replace(old_post_block, debug_login_start)
        
        with open('routes/auth.py', 'w') as f:
            f.write(new_auth_content)
        
        print("✅ Added debugging to auth.login route")
    else:
        print("❌ Could not find login POST handler in auth.py")
    
    # 3. Create a debug info script
    debug_info_script = '''#!/usr/bin/env python3
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
    print("\\n📊 DATABASE STATUS:")
    if os.path.exists('instance/accessible_outings.db'):
        conn = sqlite3.connect('instance/accessible_outings.db')
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
    print("\\n⚙️ CONFIGURATION:")
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
    print("\\n📄 TEMPLATES:")
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
    
    print("\\n🚀 NEXT STEPS:")
    print("1. Restart Flask application")
    print("2. Try login with admin/password")
    print("3. Check Flask console for debug messages")
    print("4. Look for messages starting with 🔍, 👤, 🔐, ✅, ❌")

if __name__ == '__main__':
    show_debug_info()
'''
    
    with open('debug_auth_info.py', 'w') as f:
        f.write(debug_info_script)
    
    print("✅ Created debug_auth_info.py")
    
    print("\n🎯 DEBUGGING ENABLED!")
    print("=" * 50)
    print("1. Restart your Flask application")
    print("2. Try logging in with admin/password")
    print("3. Check the Flask console output for detailed debug messages")
    print("4. Run: python debug_auth_info.py for system status")
    print("\nLook for these debug symbols in Flask console:")
    print("🔍 = Authentication start")
    print("👤 = User lookup result")
    print("🔐 = Password checking")
    print("✅ = Success")
    print("❌ = Failure")

if __name__ == '__main__':
    enable_flask_debugging()