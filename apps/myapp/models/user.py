from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    """User model for authentication and user preferences."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    home_zip_code = db.Column(db.String(10))
    max_travel_minutes = db.Column(db.Integer, default=60)
    accessibility_needs = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    favorites = db.relationship('UserFavorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('UserReview', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, first_name=None, last_name=None, 
                 home_zip_code=None, max_travel_minutes=60, accessibility_needs=None, is_admin=False):
        """Initialize a new user."""
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.home_zip_code = home_zip_code
        self.max_travel_minutes = max_travel_minutes
        self.accessibility_needs = accessibility_needs
        self.is_admin = is_admin
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_favorite_venues(self):
        """Get all venues favorited by this user."""
        from .venue import Venue
        return Venue.query.join(UserFavorite).filter(UserFavorite.user_id == self.id).all()
    
    def is_venue_favorited(self, venue_id):
        """Check if a venue is favorited by this user."""
        from .review import UserFavorite
        return UserFavorite.query.filter_by(user_id=self.id, venue_id=venue_id).first() is not None
    
    def get_venue_review(self, venue_id):
        """Get this user's review for a specific venue."""
        from .review import UserReview
        return UserReview.query.filter_by(user_id=self.id, venue_id=venue_id).first()
    
    def get_recent_searches(self, limit=10):
        """Get the user's recent search history."""
        from .review import SearchHistory
        return SearchHistory.query.filter_by(user_id=self.id)\
                                 .order_by(SearchHistory.created_at.desc())\
                                 .limit(limit).all()
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'home_zip_code': self.home_zip_code,
            'max_travel_minutes': self.max_travel_minutes,
            'accessibility_needs': self.accessibility_needs,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_user(username, email, password, **kwargs):
        """Create a new user with validation."""
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        
        # Create new user
        user = User(username=username, email=email, password=password, **kwargs)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate a user by username/email and password."""
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            return user
        return None
    
    def __repr__(self):
        return f'<User {self.username}>'
