from datetime import datetime, date, time, timedelta
from flask_sqlalchemy import SQLAlchemy
from . import db
from utils.database import DatabaseCompatArray

class Event(db.Model):
    """Event model for storing event information with accessibility and experience details."""
    
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic event information
    title = db.Column(db.String(500), nullable=False, index=True)
    description = db.Column(db.Text)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    
    # Event timing
    start_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time)
    end_date = db.Column(db.Date)
    end_time = db.Column(db.Time)
    duration_hours = db.Column(db.Float)  # For events without specific end time
    
    # Event categorization - Fun, Interesting, Off-beat
    is_fun = db.Column(db.Boolean, default=False, index=True)
    is_interesting = db.Column(db.Boolean, default=False, index=True) 
    is_off_beat = db.Column(db.Boolean, default=False, index=True)
    
    # Event details
    cost = db.Column(db.String(100))  # Free, $25, $10-20, etc.
    registration_required = db.Column(db.Boolean, default=False)
    registration_url = db.Column(db.String(500))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    
    # Capacity and audience
    max_participants = db.Column(db.Integer)
    age_restriction = db.Column(db.String(50))  # "All ages", "18+", "Kids only", etc.
    audience_type = db.Column(db.String(100))  # "Families", "Adults", "Seniors", etc.
    
    # Accessibility information
    wheelchair_accessible = db.Column(db.Boolean, default=False, index=True)
    hearing_accessible = db.Column(db.Boolean, default=False)  # Sign language, hearing loops
    vision_accessible = db.Column(db.Boolean, default=False)   # Audio descriptions, large print
    mobility_accommodations = db.Column(db.Text)
    accessibility_notes = db.Column(db.Text)
    
    # Event characteristics
    indoor_outdoor = db.Column(db.String(20))  # "Indoor", "Outdoor", "Both"
    weather_dependent = db.Column(db.Boolean, default=False)
    bring_items = db.Column(db.Text)  # What to bring
    provided_items = db.Column(db.Text)  # What's provided
    
    # Experience tags and scoring
    experience_tags = db.Column(DatabaseCompatArray())  # ['hands-on', 'educational', 'creative']
    fun_score = db.Column(db.Numeric(3, 2), default=0.0)  # 0.0-10.0 scale
    learning_potential = db.Column(db.Numeric(3, 2), default=0.0)  # 0.0-10.0 scale
    uniqueness_score = db.Column(db.Numeric(3, 2), default=0.0)  # 0.0-10.0 scale
    
    # External links and media
    event_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    social_media_links = db.Column(DatabaseCompatArray())
    
    # Metadata
    source = db.Column(db.String(100))  # Where event info came from
    external_id = db.Column(db.String(255))  # ID from external source
    source_api = db.Column(db.String(50))  # API source: 'eventbrite', 'meetup', etc.
    external_event_id = db.Column(db.String(100))  # Original API event ID
    last_verified = db.Column(db.DateTime)  # When event was last verified as still active
    verification_status = db.Column(db.String(20), default='unverified')  # 'verified', 'expired', 'removed', 'unverified'
    api_data = db.Column(db.JSON)  # Store raw API response for debugging
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(100))  # "Weekly", "Monthly", etc.
    
    # Relationships
    venue = db.relationship('Venue', backref='events', lazy=True)
    favorites = db.relationship('EventFavorite', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('EventReview', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, venue_id, start_date, **kwargs):
        """Initialize a new event."""
        self.title = title
        self.venue_id = venue_id
        self.start_date = start_date
        
        # Set other attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def event_datetime(self):
        """Get combined start datetime."""
        if self.start_time:
            return datetime.combine(self.start_date, self.start_time)
        return datetime.combine(self.start_date, time(0, 0))
    
    @property
    def end_datetime(self):
        """Get combined end datetime."""
        if self.end_date and self.end_time:
            return datetime.combine(self.end_date, self.end_time)
        elif self.end_date:
            return datetime.combine(self.end_date, time(23, 59))
        elif self.start_time and self.duration_hours:
            start_dt = self.event_datetime
            return start_dt + timedelta(hours=self.duration_hours)
        return None
    
    @property
    def is_today(self):
        """Check if event is today."""
        return self.start_date == date.today()
    
    @property
    def is_upcoming(self):
        """Check if event is upcoming."""
        return self.start_date >= date.today()
    
    @property
    def is_past(self):
        """Check if event is past."""
        return self.start_date < date.today()
    
    @property
    def is_this_week(self):
        """Check if event is this week."""
        today = date.today()
        days_ahead = 6 - today.weekday()  # Days until Sunday
        end_of_week = today + timedelta(days=days_ahead)
        return today <= self.start_date <= end_of_week
    
    def get_event_types(self):
        """Get list of event types (fun, interesting, off-beat)."""
        types = []
        if self.is_fun:
            types.append('Fun')
        if self.is_interesting:
            types.append('Interesting')
        if self.is_off_beat:
            types.append('Off-beat')
        return types
    
    def get_accessibility_score(self):
        """Calculate accessibility score based on available features."""
        features = [
            self.wheelchair_accessible,
            self.hearing_accessible,
            self.vision_accessible,
            bool(self.mobility_accommodations),
            bool(self.accessibility_notes)
        ]
        return round((sum(1 for feature in features if feature) / len(features)) * 100, 2)
    
    def get_time_display(self):
        """Get formatted time display."""
        if self.start_time and self.end_time:
            start = self.start_time.strftime('%I:%M %p').lstrip('0')
            end = self.end_time.strftime('%I:%M %p').lstrip('0')
            return f"{start} - {end}"
        elif self.start_time:
            return self.start_time.strftime('%I:%M %p').lstrip('0')
        return "Time TBA"
    
    def get_date_display(self):
        """Get formatted date display."""
        if self.end_date and self.end_date != self.start_date:
            start = self.start_date.strftime('%B %d')
            end = self.end_date.strftime('%B %d, %Y')
            return f"{start} - {end}"
        return self.start_date.strftime('%B %d, %Y')
    
    def get_duration_display(self):
        """Get formatted duration display."""
        if self.duration_hours:
            if self.duration_hours == 1.0:
                return "1 hour"
            elif self.duration_hours < 1.0:
                minutes = int(self.duration_hours * 60)
                return f"{minutes} minutes"
            else:
                return f"{self.duration_hours:.1f} hours"
        elif self.start_time and self.end_time:
            start_dt = datetime.combine(self.start_date, self.start_time)
            end_dt = datetime.combine(self.end_date or self.start_date, self.end_time)
            duration = end_dt - start_dt
            hours = duration.total_seconds() / 3600
            if hours == 1.0:
                return "1 hour"
            elif hours < 1.0:
                minutes = int(duration.total_seconds() / 60)
                return f"{minutes} minutes"
            else:
                return f"{hours:.1f} hours"
        return "Duration varies"
    
    def calculate_fun_score(self):
        """Calculate fun score based on event characteristics."""
        score = 0.0
        
        # Base score for different types
        if self.is_fun:
            score += 7.0
        if self.is_off_beat:
            score += 2.0  # Off-beat events are often fun
        
        # Activity-based scoring
        fun_keywords = [
            'paint', 'art', 'craft', 'create', 'make', 'build', 'dance', 'music',
            'game', 'play', 'festival', 'party', 'celebration', 'comedy', 'magic',
            'cooking', 'baking', 'workshop', 'hands-on', 'interactive'
        ]
        
        title_lower = self.title.lower()
        desc_lower = (self.description or '').lower()
        text = f"{title_lower} {desc_lower}"
        
        keyword_matches = sum(1 for keyword in fun_keywords if keyword in text)
        score += min(keyword_matches * 0.5, 2.0)  # Max 2.0 from keywords
        
        # Experience tags boost
        if self.experience_tags:
            fun_tags = ['hands-on', 'interactive', 'creative', 'social', 'entertaining']
            tag_boost = sum(1.0 for tag in self.experience_tags if tag in fun_tags)
            score += min(tag_boost * 0.3, 1.0)  # Max 1.0 from tags
        
        return min(score, 10.0)
    
    def calculate_learning_potential(self):
        """Calculate learning potential score."""
        score = 0.0
        
        if self.is_interesting:
            score += 7.0
        
        learning_keywords = [
            'learn', 'education', 'class', 'course', 'workshop', 'seminar', 'lecture',
            'training', 'skill', 'technique', 'history', 'science', 'nature',
            'demonstration', 'expert', 'master', 'professional'
        ]
        
        title_lower = self.title.lower()
        desc_lower = (self.description or '').lower()
        text = f"{title_lower} {desc_lower}"
        
        keyword_matches = sum(1 for keyword in learning_keywords if keyword in text)
        score += min(keyword_matches * 0.4, 2.5)
        
        if self.experience_tags:
            learning_tags = ['educational', 'informative', 'skill-building', 'expert-led']
            tag_boost = sum(1.0 for tag in self.experience_tags if tag in learning_tags)
            score += min(tag_boost * 0.5, 1.5)
        
        return min(score, 10.0)
    
    def calculate_uniqueness_score(self):
        """Calculate uniqueness/off-beat score."""
        score = 0.0
        
        if self.is_off_beat:
            score += 8.0
        
        unique_keywords = [
            'unusual', 'unique', 'rare', 'exclusive', 'limited', 'special', 'mystery',
            'ghost', 'haunted', 'secret', 'hidden', 'underground', 'behind-scenes',
            'tour', 'adventure', 'exploration', 'discovery'
        ]
        
        title_lower = self.title.lower()
        desc_lower = (self.description or '').lower()
        text = f"{title_lower} {desc_lower}"
        
        keyword_matches = sum(1 for keyword in unique_keywords if keyword in text)
        score += min(keyword_matches * 0.6, 2.0)
        
        return min(score, 10.0)
    
    def update_scores(self):
        """Update all calculated scores."""
        self.fun_score = self.calculate_fun_score()
        self.learning_potential = self.calculate_learning_potential()
        self.uniqueness_score = self.calculate_uniqueness_score()
        self.last_updated = datetime.utcnow()
    
    def to_dict(self):
        """Convert event to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'venue': self.venue.to_dict() if self.venue else None,
            'start_date': self.start_date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'event_types': self.get_event_types(),
            'is_fun': self.is_fun,
            'is_interesting': self.is_interesting,
            'is_off_beat': self.is_off_beat,
            'cost': self.cost,
            'registration_required': self.registration_required,
            'registration_url': self.registration_url,
            'wheelchair_accessible': self.wheelchair_accessible,
            'accessibility_score': self.get_accessibility_score(),
            'time_display': self.get_time_display(),
            'date_display': self.get_date_display(),
            'duration_display': self.get_duration_display(),
            'fun_score': float(self.fun_score) if self.fun_score else 0.0,
            'learning_potential': float(self.learning_potential) if self.learning_potential else 0.0,
            'uniqueness_score': float(self.uniqueness_score) if self.uniqueness_score else 0.0,
            'experience_tags': self.experience_tags or [],
            'event_url': self.event_url,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def search_events(start_date=None, end_date=None, event_types=None, 
                     wheelchair_accessible_only=False, venue_ids=None):
        """Search for events with filters."""
        query = Event.query
        
        # Date filtering
        if start_date:
            query = query.filter(Event.start_date >= start_date)
        if end_date:
            query = query.filter(Event.start_date <= end_date)
        
        # Event type filtering
        if event_types:
            conditions = []
            if 'fun' in event_types:
                conditions.append(Event.is_fun == True)
            if 'interesting' in event_types:
                conditions.append(Event.is_interesting == True)
            if 'off_beat' in event_types:
                conditions.append(Event.is_off_beat == True)
            
            if conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))
        
        # Accessibility filtering
        if wheelchair_accessible_only:
            query = query.filter(Event.wheelchair_accessible == True)
        
        # Venue filtering
        if venue_ids:
            query = query.filter(Event.venue_id.in_(venue_ids))
        
        return query.order_by(Event.start_date, Event.start_time).all()
    
    @staticmethod
    def get_todays_events():
        """Get all events happening today."""
        today = date.today()
        return Event.query.filter(Event.start_date == today)\
                         .order_by(Event.start_time).all()
    
    @staticmethod
    def get_upcoming_events(days=7):
        """Get upcoming events within specified days."""
        today = date.today()
        end_date = today + timedelta(days=days)
        return Event.query.filter(
            Event.start_date >= today,
            Event.start_date <= end_date
        ).order_by(Event.start_date, Event.start_time).all()
    
    def __repr__(self):
        return f'<Event {self.title} on {self.start_date}>'


class EventFavorite(db.Model):
    """User favorites for events."""
    
    __tablename__ = 'event_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    notes = db.Column(db.Text)
    reminder_set = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id'),)


class EventReview(db.Model):
    """User reviews for events."""
    
    __tablename__ = 'event_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    attended = db.Column(db.Boolean, default=True)
    overall_rating = db.Column(db.Integer)  # 1-5 scale
    accessibility_rating = db.Column(db.Integer)  # 1-5 scale
    fun_rating = db.Column(db.Integer)  # 1-5 scale
    
    review_text = db.Column(db.Text)
    accessibility_notes = db.Column(db.Text)
    would_attend_again = db.Column(db.Boolean)
    would_recommend = db.Column(db.Boolean)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='event_reviews', lazy=True)