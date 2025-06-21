import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    # Check if authentication is bypassed
    if current_app.config.get('BYPASS_AUTH'):
        default_user = User.query.get(current_app.config.get('DEFAULT_USER_ID', 1))
        if default_user:
            login_user(default_user)
            flash('Logged in automatically (development mode)', 'info')
            return redirect(url_for('main.index'))
        else:
            flash('Default user not found. Please create a user account.', 'error')
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
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
        logger.debug(f"👤 Authentication result: {user.username if user else 'None'}")
        
        if user:
            login_user(user, remember=remember_me)
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        home_zip_code = request.form.get('home_zip_code')
        max_travel_minutes = request.form.get('max_travel_minutes', 60, type=int)
        accessibility_needs = request.form.get('accessibility_needs')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please provide a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Validate ZIP code if provided
        if home_zip_code:
            from utils.geocoding import GeocodingService
            geocoding = GeocodingService(current_app.config['GOOGLE_PLACES_API_KEY'])
            if not geocoding.validate_zip_code(home_zip_code):
                errors.append('Please provide a valid ZIP code.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            user = User.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                home_zip_code=home_zip_code,
                max_travel_minutes=max_travel_minutes,
                accessibility_needs=accessibility_needs
            )
            
            flash(f'Registration successful! Welcome, {user.full_name}!', 'success')
            login_user(user)
            return redirect(url_for('main.index'))
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            current_app.logger.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.home_zip_code = request.form.get('home_zip_code')
        current_user.max_travel_minutes = request.form.get('max_travel_minutes', 60, type=int)
        current_user.accessibility_needs = request.form.get('accessibility_needs')
        
        # Validate ZIP code if provided
        if current_user.home_zip_code:
            from utils.geocoding import GeocodingService
            geocoding = GeocodingService(current_app.config['GOOGLE_PLACES_API_KEY'])
            if not geocoding.validate_zip_code(current_user.home_zip_code):
                flash('Please provide a valid ZIP code.', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile update error: {e}")
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change error: {e}")
            flash('Failed to change password. Please try again.', 'error')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Delete user account."""
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_delete = request.form.get('confirm_delete')
        
        if not current_user.check_password(password):
            flash('Password is incorrect.', 'error')
            return render_template('auth/delete_account.html')
        
        if confirm_delete != 'DELETE':
            flash('Please type "DELETE" to confirm account deletion.', 'error')
            return render_template('auth/delete_account.html')
        
        try:
            username = current_user.username
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash(f'Account {username} has been deleted.', 'info')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Account deletion error: {e}")
            flash('Failed to delete account. Please try again.', 'error')
    
    return render_template('auth/delete_account.html')
