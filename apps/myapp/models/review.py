from datetime import datetime, timedelta
from . import db
from utils.database import DatabaseCompatArray, DatabaseCompatJSON

class UserFavorite(db.Model):
    """User favorites model for saving preferred venues."""
    
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    notes = db.Column(db.Text)
    personal_accessibility_rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'venue_id', name='unique_user_venue_favorite'),)
    
    def __init__(self, user_id, venue_id, notes=None, personal_accessibility_rating=None):
        """Initialize a new favorite."""
        self.user_id = user_id
        self.venue_id = venue_id
        self.notes = notes
        self.personal_accessibility_rating = personal_accessibility_rating
    
    def to_dict(self):
        """Convert favorite to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'venue_id': self.venue_id,
            'notes': self.notes,
            'personal_accessibility_rating': self.personal_accessibility_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'venue': self.venue.to_dict() if self.venue else None
        }
    
    @staticmethod
    def add_favorite(user_id, venue_id, notes=None, personal_accessibility_rating=None):
        """Add a venue to user's favorites."""
        # Check if already favorited
        existing = UserFavorite.query.filter_by(user_id=user_id, venue_id=venue_id).first()
        if existing:
            # Update existing favorite
            existing.notes = notes
            existing.personal_accessibility_rating = personal_accessibility_rating
            db.session.commit()
            return existing
        
        # Create new favorite
        favorite = UserFavorite(user_id, venue_id, notes, personal_accessibility_rating)
        db.session.add(favorite)
        db.session.commit()
        return favorite
    
    @staticmethod
    def remove_favorite(user_id, venue_id):
        """Remove a venue from user's favorites."""
        favorite = UserFavorite.query.filter_by(user_id=user_id, venue_id=venue_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return True
        return False
    
    def __repr__(self):
        return f'<UserFavorite user_id={self.user_id} venue_id={self.venue_id}>'

class UserReview(db.Model):
    """User reviews and visit logs for venues."""
    
    __tablename__ = 'user_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    visit_date = db.Column(db.Date)
    overall_rating = db.Column(db.Integer)  # 1-5 scale
    accessibility_rating = db.Column(db.Integer)  # 1-5 scale
    review_text = db.Column(db.Text)
    accessibility_notes = db.Column(db.Text)
    would_return = db.Column(db.Boolean)
    recommended_for_wheelchair = db.Column(db.Boolean)
    photos = db.Column(DatabaseCompatArray())  # Array of photo URLs/paths
    weather_conditions = db.Column(db.String(100))
    visit_duration_hours = db.Column(db.Numeric(3, 1))
    companion_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, venue_id, **kwargs):
        """Initialize a new review."""
        self.user_id = user_id
        self.venue_id = venue_id
        
        # Set other attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_recent(self):
        """Check if the review was created recently (within 30 days)."""
        if not self.created_at:
            return False
        return (datetime.utcnow() - self.created_at).days <= 30
    
    @property
    def visit_date_formatted(self):
        """Get formatted visit date."""
        if self.visit_date:
            return self.visit_date.strftime('%B %d, %Y')
        return None
    
    def to_dict(self):
        """Convert review to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'venue_id': self.venue_id,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_date_formatted': self.visit_date_formatted,
            'overall_rating': self.overall_rating,
            'accessibility_rating': self.accessibility_rating,
            'review_text': self.review_text,
            'accessibility_notes': self.accessibility_notes,
            'would_return': self.would_return,
            'recommended_for_wheelchair': self.recommended_for_wheelchair,
            'photos': self.photos or [],
            'weather_conditions': self.weather_conditions,
            'visit_duration_hours': float(self.visit_duration_hours) if self.visit_duration_hours else None,
            'companion_count': self.companion_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_recent': self.is_recent,
            'user': {
                'username': self.user.username,
                'full_name': self.user.full_name
            } if self.user else None,
            'venue': {
                'name': self.venue.name,
                'address': self.venue.address
            } if self.venue else None
        }
    
    @staticmethod
    def get_recent_reviews(limit=10):
        """Get recent reviews across all venues."""
        return UserReview.query.order_by(UserReview.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_venue_reviews(venue_id, limit=None):
        """Get reviews for a specific venue."""
        query = UserReview.query.filter_by(venue_id=venue_id)\
                                .order_by(UserReview.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_user_reviews(user_id, limit=None):
        """Get reviews by a specific user."""
        query = UserReview.query.filter_by(user_id=user_id)\
                                .order_by(UserReview.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def __repr__(self):
        return f'<UserReview user_id={self.user_id} venue_id={self.venue_id}>'

class SearchHistory(db.Model):
    """Search history for improving recommendations and analytics."""
    
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    search_zip = db.Column(db.String(10))
    search_radius = db.Column(db.Integer)
    category_filter = db.Column(db.Integer, db.ForeignKey('venue_categories.id'))
    results_count = db.Column(db.Integer)
    accessibility_filter = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to category
    category = db.relationship('VenueCategory', backref='search_history')
    
    def __init__(self, user_id, search_zip=None, search_radius=None, 
                 category_filter=None, results_count=0, accessibility_filter=False):
        """Initialize a new search history entry."""
        self.user_id = user_id
        self.search_zip = search_zip
        self.search_radius = search_radius
        self.category_filter = category_filter
        self.results_count = results_count
        self.accessibility_filter = accessibility_filter
    
    def to_dict(self):
        """Convert search history to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'search_zip': self.search_zip,
            'search_radius': self.search_radius,
            'category_filter': self.category_filter,
            'category_name': self.category.name if self.category else None,
            'results_count': self.results_count,
            'accessibility_filter': self.accessibility_filter,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def log_search(user_id, search_zip=None, search_radius=None, 
                   category_filter=None, results_count=0, accessibility_filter=False):
        """Log a search for analytics and recommendations."""
        search = SearchHistory(user_id, search_zip, search_radius, 
                             category_filter, results_count, accessibility_filter)
        db.session.add(search)
        db.session.commit()
        return search
    
    @staticmethod
    def get_popular_searches(days=30, limit=10):
        """Get popular search patterns from the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.session.query(
            SearchHistory.search_zip,
            SearchHistory.category_filter,
            db.func.count(SearchHistory.id).label('search_count')
        ).filter(
            SearchHistory.created_at >= cutoff_date
        ).group_by(
            SearchHistory.search_zip,
            SearchHistory.category_filter
        ).order_by(
            db.func.count(SearchHistory.id).desc()
        ).limit(limit).all()
    
    def __repr__(self):
        return f'<SearchHistory user_id={self.user_id} zip={self.search_zip}>'

class ApiCache(db.Model):
    """Cache for API responses to improve performance and reduce API calls."""
    
    __tablename__ = 'api_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    cache_data = db.Column(DatabaseCompatJSON(), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, cache_key, cache_data, expires_at=None, ttl_hours=24):
        """Initialize a new cache entry."""
        self.cache_key = cache_key
        self.cache_data = cache_data
        if expires_at:
            self.expires_at = expires_at
        else:
            self.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    @property
    def is_expired(self):
        """Check if the cache entry has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """Convert cache entry to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'cache_data': self.cache_data,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired
        }
    
    @staticmethod
    def get_cached_data(cache_key):
        """Get cached data if it exists and hasn't expired."""
        cache_entry = ApiCache.query.filter_by(cache_key=cache_key).first()
        if cache_entry and not cache_entry.is_expired:
            return cache_entry.cache_data
        elif cache_entry and cache_entry.is_expired:
            # Clean up expired entry
            db.session.delete(cache_entry)
            db.session.commit()
        return None
    
    @staticmethod
    def set_cached_data(cache_key, cache_data, ttl_hours=24):
        """Set cached data with expiration."""
        # Remove existing cache entry if it exists
        existing = ApiCache.query.filter_by(cache_key=cache_key).first()
        if existing:
            db.session.delete(existing)
        
        # Create new cache entry
        cache_entry = ApiCache(cache_key, cache_data, ttl_hours=ttl_hours)
        db.session.add(cache_entry)
        db.session.commit()
        return cache_entry
    
    @staticmethod
    def clean_expired_cache():
        """Remove all expired cache entries."""
        expired_entries = ApiCache.query.filter(ApiCache.expires_at < datetime.utcnow()).all()
        for entry in expired_entries:
            db.session.delete(entry)
        db.session.commit()
        return len(expired_entries)
    
    @staticmethod
    def clear_cache_by_pattern(pattern):
        """Clear cache entries matching a pattern."""
        entries = ApiCache.query.filter(ApiCache.cache_key.like(f'%{pattern}%')).all()
        for entry in entries:
            db.session.delete(entry)
        db.session.commit()
        return len(entries)
    
    def __repr__(self):
        return f'<ApiCache {self.cache_key}>'
