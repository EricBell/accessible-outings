from datetime import datetime
from math import radians, cos
from . import db
from utils.database import DatabaseCompatArray

class VenueCategory(db.Model):
    """Venue category model for organizing venues by type."""
    
    __tablename__ = 'venue_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    # name = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(128), unique=True, nullable=False)  # Add unique=True
    description = db.Column(db.Text)
    icon_class = db.Column(db.String(50))  # CSS class for icons
    search_keywords = db.Column(DatabaseCompatArray())  # Keywords for API searches
    
    # Relationships
    venues = db.relationship('Venue', backref='category', lazy='dynamic')
    
    def __init__(self, name, description=None, icon_class=None, search_keywords=None):
        """Initialize a new venue category."""
        self.name = name
        self.description = description
        self.icon_class = icon_class
        self.search_keywords = search_keywords or []
    
    def get_venues_count(self):
        """Get the number of venues in this category."""
        return self.venues.count()
    
    def get_accessible_venues_count(self):
        """Get the number of wheelchair accessible venues in this category."""
        return self.venues.filter_by(wheelchair_accessible=True).count()
    
    def to_dict(self):
        """Convert category to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon_class': self.icon_class,
            'search_keywords': self.search_keywords,
            'venues_count': self.get_venues_count(),
            'accessible_venues_count': self.get_accessible_venues_count()
        }
    
    def __repr__(self):
        return f'<VenueCategory {self.name}>'

class Venue(db.Model):
    """Venue model for storing venue information and accessibility details."""
    
    __tablename__ = 'venues'
    
    id = db.Column(db.Integer, primary_key=True)
    google_place_id = db.Column(db.String(255), unique=True, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(500))
    latitude = db.Column(db.Numeric(10, 8), index=True)
    longitude = db.Column(db.Numeric(11, 8), index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('venue_categories.id'))
    google_rating = db.Column(db.Numeric(2, 1))
    price_level = db.Column(db.Integer)  # 0-4 scale from Google
    
    # Accessibility features
    wheelchair_accessible = db.Column(db.Boolean, default=False, index=True)
    accessible_parking = db.Column(db.Boolean, default=False)
    accessible_restroom = db.Column(db.Boolean, default=False)
    elevator_access = db.Column(db.Boolean, default=False)
    wide_doorways = db.Column(db.Boolean, default=False)
    ramp_access = db.Column(db.Boolean, default=False)
    accessible_seating = db.Column(db.Boolean, default=False)
    accessibility_notes = db.Column(db.Text)
    
    # Operating hours
    hours_monday = db.Column(db.String(50))
    hours_tuesday = db.Column(db.String(50))
    hours_wednesday = db.Column(db.String(50))
    hours_thursday = db.Column(db.String(50))
    hours_friday = db.Column(db.String(50))
    hours_saturday = db.Column(db.String(50))
    hours_sunday = db.Column(db.String(50))
    seasonal_hours = db.Column(db.Text)
    
    # Metadata
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_accessible = db.Column(db.Boolean, default=False)
    photo_urls = db.Column(DatabaseCompatArray())
    
    # Relationships
    favorites = db.relationship('UserFavorite', backref='venue', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('UserReview', backref='venue', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, address, latitude=None, longitude=None, **kwargs):
        """Initialize a new venue."""
        self.name = name
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        
        # Set other attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def full_address(self):
        """Get the full formatted address."""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        return ', '.join(parts)
    
    @property
    def accessibility_score(self):
        """Calculate an accessibility score based on available features."""
        features = [
            self.wheelchair_accessible,
            self.accessible_parking,
            self.accessible_restroom,
            self.elevator_access,
            self.wide_doorways,
            self.ramp_access,
            self.accessible_seating
        ]
        return sum(1 for feature in features if feature) / len(features) * 100
    
    @property
    def accessibility_features_list(self):
        """Get a list of available accessibility features."""
        features = []
        if self.wheelchair_accessible:
            features.append("Wheelchair Accessible")
        if self.accessible_parking:
            features.append("Accessible Parking")
        if self.accessible_restroom:
            features.append("Accessible Restroom")
        if self.elevator_access:
            features.append("Elevator Access")
        if self.wide_doorways:
            features.append("Wide Doorways")
        if self.ramp_access:
            features.append("Ramp Access")
        if self.accessible_seating:
            features.append("Accessible Seating")
        return features
    
    def get_hours_for_day(self, day_name):
        """Get operating hours for a specific day."""
        day_attr = f"hours_{day_name.lower()}"
        return getattr(self, day_attr, None)
    
    def get_all_hours(self):
        """Get all operating hours as a dictionary."""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        return {day: self.get_hours_for_day(day) for day in days}
    
    def is_open_today(self):
        """Check if the venue is open today (basic implementation)."""
        from datetime import datetime
        today = datetime.now().strftime('%A').lower()
        hours = self.get_hours_for_day(today)
        return hours and hours.lower() not in ['closed', 'close']
    
    def get_average_rating(self):
        """Get the average user rating for this venue."""
        if self.reviews.count() == 0:
            return self.google_rating
        
        user_ratings = [review.overall_rating for review in self.reviews if review.overall_rating]
        if not user_ratings:
            return self.google_rating
        
        return sum(user_ratings) / len(user_ratings)
    
    def get_average_accessibility_rating(self):
        """Get the average accessibility rating from user reviews."""
        accessibility_ratings = [review.accessibility_rating for review in self.reviews 
                               if review.accessibility_rating]
        if not accessibility_ratings:
            return None
        
        return sum(accessibility_ratings) / len(accessibility_ratings)
    
    def get_user_reviews_count(self):
        """Get the number of user reviews for this venue."""
        return self.reviews.count()
    
    def get_favorites_count(self):
        """Get the number of users who have favorited this venue."""
        return self.favorites.count()
    
    def distance_from(self, latitude, longitude):
        """Calculate distance from given coordinates (in miles)."""
        if not self.latitude or not self.longitude:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [float(self.latitude), float(self.longitude), 
                                              latitude, longitude])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        return c * r
    
    def to_dict(self, user_latitude=None, user_longitude=None):
        """Convert venue to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'google_place_id': self.google_place_id,
            'name': self.name,
            'address': self.address,
            'full_address': self.full_address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'website': self.website,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'category': self.category.to_dict() if self.category else None,
            'google_rating': float(self.google_rating) if self.google_rating else None,
            'price_level': self.price_level,
            'wheelchair_accessible': self.wheelchair_accessible,
            'accessible_parking': self.accessible_parking,
            'accessible_restroom': self.accessible_restroom,
            'elevator_access': self.elevator_access,
            'wide_doorways': self.wide_doorways,
            'ramp_access': self.ramp_access,
            'accessible_seating': self.accessible_seating,
            'accessibility_notes': self.accessibility_notes,
            'accessibility_score': self.accessibility_score,
            'accessibility_features': self.accessibility_features_list,
            'hours': self.get_all_hours(),
            'seasonal_hours': self.seasonal_hours,
            'is_open_today': self.is_open_today(),
            'verified_accessible': self.verified_accessible,
            'photo_urls': self.photo_urls or [],
            'average_rating': self.get_average_rating(),
            'average_accessibility_rating': self.get_average_accessibility_rating(),
            'user_reviews_count': self.get_user_reviews_count(),
            'favorites_count': self.get_favorites_count(),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add distance if user coordinates provided
        if user_latitude and user_longitude:
            distance = self.distance_from(user_latitude, user_longitude)
            data['distance_miles'] = round(distance, 1) if distance else None
        
        return data
    
    @staticmethod
    def find_by_google_place_id(place_id):
        """Find venue by Google Place ID."""
        return Venue.query.filter_by(google_place_id=place_id).first()
    
    @staticmethod
    def search_nearby(latitude, longitude, radius_miles=30, category_id=None, 
                     wheelchair_accessible_only=False):
        """Search for venues near given coordinates."""
        # This is a simplified search - in production, you'd want to use PostGIS
        # or a more sophisticated geographic search
        query = Venue.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if wheelchair_accessible_only:
            query = query.filter_by(wheelchair_accessible=True)
        
        # Basic distance filtering (not precise, but functional)
        # In production, use proper geographic queries
        lat_range = radius_miles / 69.0  # Approximate miles per degree latitude
        lon_range = radius_miles / (69.0 * abs(cos(radians(latitude))))
        
        query = query.filter(
            Venue.latitude.between(latitude - lat_range, latitude + lat_range),
            Venue.longitude.between(longitude - lon_range, longitude + lon_range)
        )
        
        return query.all()
    
    def __repr__(self):
        return f'<Venue {self.name}>'
