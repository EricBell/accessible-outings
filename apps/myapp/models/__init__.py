from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Import models after db initialization to avoid circular imports
from .user import User
from .venue import Venue, VenueCategory
from .review import UserReview, UserFavorite, SearchHistory, ApiCache

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

# Export all models for easy importing
__all__ = [
    'db',
    'login_manager',
    'User',
    'Venue',
    'VenueCategory',
    'UserReview',
    'UserFavorite',
    'SearchHistory',
    'ApiCache'
]
