#!/usr/bin/env python3
"""
Create sample events for testing the events system.

This script creates realistic events for various venues in the Plaistow, NH and Boston, MA areas.
"""

import os
import sys
from datetime import date, time, datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.venue import Venue
from models.event import Event

def create_sample_events():
    """Create sample events for testing."""
    app = create_app()
    
    with app.app_context():
        # Get some venues to attach events to
        venues = Venue.query.limit(10).all()
        
        if not venues:
            print("No venues found. Please run venue search first.")
            return
        
        # Sample events with different types
        sample_events = [
            # Fun events
            {
                'title': 'Acrylic Painting Class: Paint Your Cat',
                'description': 'Learn to paint a portrait of your beloved cat using acrylic paints. All materials provided. Bring a photo of your cat!',
                'is_fun': True,
                'start_date': date.today(),
                'start_time': time(14, 0),
                'end_time': time(16, 0),
                'cost': '$45',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['hands-on', 'creative', 'social', 'beginner-friendly'],
                'audience_type': 'All ages'
            },
            {
                'title': 'Pottery Wheel Workshop',
                'description': 'Try your hand at the pottery wheel in this beginner-friendly class. Create your own ceramic bowl or mug.',
                'is_fun': True,
                'start_date': date.today() + timedelta(days=1),
                'start_time': time(10, 0),
                'duration_hours': 2.5,
                'cost': '$65',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['hands-on', 'creative', 'messy', 'therapeutic'],
                'audience_type': 'Adults'
            },
            {
                'title': 'Craft Beer Tasting & Pairing',
                'description': 'Sample local craft beers paired with artisanal cheeses. Learn about brewing processes and flavor profiles.',
                'is_fun': True,
                'start_date': date.today() + timedelta(days=2),
                'start_time': time(19, 0),
                'duration_hours': 2.0,
                'cost': '$35',
                'registration_required': True,
                'wheelchair_accessible': True,
                'age_restriction': '21+',
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['social', 'educational', 'tasting'],
                'audience_type': 'Adults'
            },
            
            # Interesting events
            {
                'title': 'Organic Lawn Care & Natural Fertilizers',
                'description': 'Expert lecture on sustainable lawn care practices, soil health, and eco-friendly fertilizer alternatives.',
                'is_interesting': True,
                'start_date': date.today() + timedelta(days=3),
                'start_time': time(18, 30),
                'duration_hours': 1.5,
                'cost': 'Free',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['educational', 'environmental', 'expert-led', 'practical'],
                'audience_type': 'Homeowners'
            },
            {
                'title': 'Local History: Hidden Stories of Plaistow',
                'description': 'Discover the forgotten tales and hidden history of Plaistow through historic photographs and documents.',
                'is_interesting': True,
                'start_date': date.today() + timedelta(days=4),
                'start_time': time(14, 0),
                'duration_hours': 1.0,
                'cost': '$10',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['educational', 'historical', 'local-interest', 'storytelling'],
                'audience_type': 'All ages'
            },
            {
                'title': 'Astronomy Night: Winter Constellations',
                'description': 'Learn to identify winter constellations and observe deep-sky objects through telescopes.',
                'is_interesting': True,
                'start_date': date.today() + timedelta(days=5),
                'start_time': time(20, 0),
                'duration_hours': 2.0,
                'cost': '$15',
                'wheelchair_accessible': True,
                'weather_dependent': True,
                'indoor_outdoor': 'Both',
                'bring_items': 'Warm clothing, red flashlight if you have one',
                'experience_tags': ['educational', 'scientific', 'outdoor', 'family-friendly'],
                'audience_type': 'All ages'
            },
            
            # Off-beat events
            {
                'title': 'Ghosts of Nashua: Night Walking Tour',
                'description': 'Explore the dark and mysterious side of Nashua with this guided tour of reportedly haunted locations.',
                'is_off_beat': True,
                'start_date': date.today() + timedelta(days=6),
                'start_time': time(20, 30),
                'duration_hours': 1.5,
                'cost': '$20',
                'age_restriction': '16+',
                'wheelchair_accessible': False,  # Walking tour
                'weather_dependent': True,
                'indoor_outdoor': 'Outdoor',
                'bring_items': 'Comfortable walking shoes, flashlight',
                'experience_tags': ['spooky', 'historical', 'walking-tour', 'storytelling'],
                'audience_type': 'Adults and teens'
            },
            {
                'title': 'Underground Tunnels & Hidden Spaces Tour',
                'description': 'Discover the secret underground passages and hidden rooms beneath downtown buildings.',
                'is_off_beat': True,
                'start_date': date.today() + timedelta(days=7),
                'start_time': time(15, 0),
                'duration_hours': 1.0,
                'cost': '$25',
                'registration_required': True,
                'max_participants': 12,
                'wheelchair_accessible': False,  # Underground access
                'indoor_outdoor': 'Indoor',
                'bring_items': 'Closed-toe shoes, small flashlight',
                'experience_tags': ['unique', 'historical', 'limited-access', 'exploration'],
                'audience_type': 'Adults'
            },
            {
                'title': 'Victorian Mourning Customs Workshop',
                'description': 'Learn about unusual Victorian death and mourning traditions, including hair jewelry and post-mortem photography.',
                'is_off_beat': True,
                'is_interesting': True,  # Can be both
                'start_date': date.today() + timedelta(days=8),
                'start_time': time(13, 0),
                'duration_hours': 2.0,
                'cost': '$30',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['historical', 'unusual', 'educational', 'cultural'],
                'audience_type': 'Adults'
            },
            
            # Mixed type events
            {
                'title': 'Murder Mystery Dinner Theater',
                'description': 'Solve a murder while enjoying a three-course dinner. Audience participation encouraged!',
                'is_fun': True,
                'is_off_beat': True,
                'start_date': date.today() + timedelta(days=9),
                'start_time': time(18, 0),
                'duration_hours': 3.0,
                'cost': '$75',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['interactive', 'theatrical', 'dining', 'mystery'],
                'audience_type': 'Adults'
            }
        ]
        
        events_created = 0
        
        for i, event_data in enumerate(sample_events):
            venue = venues[i % len(venues)]  # Cycle through available venues
            
            # Create the event
            event = Event(
                title=event_data['title'],
                venue_id=venue.id,
                start_date=event_data['start_date'],
                description=event_data.get('description'),
                start_time=event_data.get('start_time'),
                end_time=event_data.get('end_time'),
                duration_hours=event_data.get('duration_hours'),
                is_fun=event_data.get('is_fun', False),
                is_interesting=event_data.get('is_interesting', False),
                is_off_beat=event_data.get('is_off_beat', False),
                cost=event_data.get('cost'),
                registration_required=event_data.get('registration_required', False),
                wheelchair_accessible=event_data.get('wheelchair_accessible', venue.wheelchair_accessible),
                indoor_outdoor=event_data.get('indoor_outdoor'),
                weather_dependent=event_data.get('weather_dependent', False),
                bring_items=event_data.get('bring_items'),
                experience_tags=event_data.get('experience_tags', []),
                audience_type=event_data.get('audience_type'),
                age_restriction=event_data.get('age_restriction'),
                max_participants=event_data.get('max_participants')
            )
            
            # Update scores
            event.update_scores()
            
            db.session.add(event)
            events_created += 1
            
            print(f"Created event: {event.title} at {venue.name}")
        
        # Commit all events
        db.session.commit()
        
        print(f"\n✅ Successfully created {events_created} sample events!")
        print("\nEvent breakdown:")
        print(f"  Fun events: {sum(1 for e in sample_events if e.get('is_fun'))}")
        print(f"  Interesting events: {sum(1 for e in sample_events if e.get('is_interesting'))}")
        print(f"  Off-beat events: {sum(1 for e in sample_events if e.get('is_off_beat'))}")
        print(f"  Today's events: {sum(1 for e in sample_events if e['start_date'] == date.today())}")

if __name__ == "__main__":
    create_sample_events()