#!/usr/bin/env python3
"""
Create Boston-area venues and events for testing.
"""

import os
import sys
from datetime import date, time, datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.venue import Venue, VenueCategory
from models.event import Event

def create_boston_venues_and_events():
    """Create Boston-area venues and events."""
    app = create_app()
    
    with app.app_context():
        # Get categories
        categories = VenueCategory.query.all()
        category_map = {cat.name: cat.id for cat in categories}
        
        # Create Boston-area venues
        boston_venues = [
            {
                'name': 'Museum of Science Boston',
                'address': '1 Science Park',
                'city': 'Boston',
                'state': 'MA',
                'zip_code': '02114',
                'latitude': 42.3676,
                'longitude': -71.0708,
                'category_id': category_map.get('Museums'),
                'wheelchair_accessible': True,
                'accessible_parking': True,
                'accessible_restroom': True,
                'elevator_access': True
            },
            {
                'name': 'New England Aquarium',
                'address': '1 Central Wharf',
                'city': 'Boston',
                'state': 'MA',
                'zip_code': '02110',
                'latitude': 42.3589,
                'longitude': -71.0493,
                'category_id': category_map.get('Aquariums'),
                'wheelchair_accessible': True,
                'accessible_parking': True,
                'accessible_restroom': True,
                'elevator_access': True
            },
            {
                'name': 'Arnold Arboretum',
                'address': '125 Arborway',
                'city': 'Jamaica Plain',
                'state': 'MA',
                'zip_code': '02130',
                'latitude': 42.3088,
                'longitude': -71.1258,
                'category_id': category_map.get('Botanical Gardens'),
                'wheelchair_accessible': True,
                'accessible_parking': True,
                'accessible_restroom': True,
                'ramp_access': True
            },
            {
                'name': 'Boston Public Library - Central',
                'address': '700 Boylston St',
                'city': 'Boston',
                'state': 'MA',
                'zip_code': '02116',
                'latitude': 42.3495,
                'longitude': -71.0777,
                'category_id': category_map.get('Libraries'),
                'wheelchair_accessible': True,
                'accessible_parking': True,
                'accessible_restroom': True,
                'elevator_access': True
            },
            {
                'name': 'MFA Boston',
                'address': '465 Huntington Ave',
                'city': 'Boston',
                'state': 'MA',
                'zip_code': '02115',
                'latitude': 42.3394,
                'longitude': -71.0948,
                'category_id': category_map.get('Art Galleries'),
                'wheelchair_accessible': True,
                'accessible_parking': True,
                'accessible_restroom': True,
                'elevator_access': True
            },
            {
                'name': 'Michaels Arts & Crafts',
                'address': '1234 Commonwealth Ave',
                'city': 'Brighton',
                'state': 'MA',
                'zip_code': '02135',
                'latitude': 42.3505,
                'longitude': -71.1567,
                'category_id': category_map.get('Craft Stores'),
                'wheelchair_accessible': True,
                'accessible_parking': True,
                'accessible_restroom': True
            }
        ]
        
        # Create venues
        created_venues = []
        for venue_data in boston_venues:
            # Check if venue already exists
            existing = Venue.query.filter_by(name=venue_data['name']).first()
            if not existing:
                venue = Venue(**venue_data)
                db.session.add(venue)
                created_venues.append(venue)
                print(f"Created venue: {venue_data['name']}")
            else:
                created_venues.append(existing)
                print(f"Using existing venue: {existing.name}")
        
        db.session.commit()
        
        # Create Boston-area events
        boston_events = [
            # Today's events
            {
                'title': 'Watercolor Painting: Boston Harbor Views',
                'description': 'Paint scenic Boston Harbor views using watercolor techniques. All skill levels welcome.',
                'venue_idx': 0,  # Museum of Science
                'is_fun': True,
                'start_date': date.today(),
                'start_time': time(10, 0),
                'duration_hours': 3.0,
                'cost': '$55',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['hands-on', 'creative', 'scenic', 'relaxing']
            },
            {
                'title': 'Marine Biology Lab: Touch Tank Experience',
                'description': 'Get hands-on with sea creatures in our accessible touch tanks. Learn about marine ecosystems.',
                'venue_idx': 1,  # Aquarium
                'is_fun': True,
                'is_interesting': True,
                'start_date': date.today(),
                'start_time': time(14, 0),
                'duration_hours': 1.5,
                'cost': '$25',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['hands-on', 'educational', 'marine-life', 'interactive']
            },
            
            # Tomorrow's events
            {
                'title': 'Urban Ecology Workshop',
                'description': 'Learn how plants adapt to city life in this educational workshop about urban ecosystems.',
                'venue_idx': 2,  # Arnold Arboretum
                'is_interesting': True,
                'start_date': date.today() + timedelta(days=1),
                'start_time': time(11, 0),
                'duration_hours': 2.0,
                'cost': '$20',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Both',
                'experience_tags': ['educational', 'nature', 'scientific', 'walking']
            },
            {
                'title': 'Pottery Wheel & Glazing Workshop',
                'description': 'Create your own ceramic piece from start to finish. Glazing techniques included.',
                'venue_idx': 5,  # Michaels
                'is_fun': True,
                'start_date': date.today() + timedelta(days=1),
                'start_time': time(13, 0),
                'duration_hours': 4.0,
                'cost': '$75',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['hands-on', 'creative', 'messy', 'artistic']
            },
            
            # Day after tomorrow
            {
                'title': 'Hidden Boston: Underground Railroad Sites',
                'description': 'Discover secret Underground Railroad locations throughout historic Boston.',
                'venue_idx': 3,  # Boston Public Library
                'is_interesting': True,
                'is_off_beat': True,
                'start_date': date.today() + timedelta(days=2),
                'start_time': time(15, 0),
                'duration_hours': 2.5,
                'cost': '$30',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Both',
                'experience_tags': ['historical', 'hidden', 'walking-tour', 'meaningful']
            },
            {
                'title': 'After Hours: Art in the Dark',
                'description': 'Experience the museum after hours with special lighting and mysterious atmosphere.',
                'venue_idx': 4,  # MFA Boston
                'is_off_beat': True,
                'start_date': date.today() + timedelta(days=2),
                'start_time': time(19, 0),
                'duration_hours': 2.0,
                'cost': '$45',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['atmospheric', 'artistic', 'exclusive', 'evening']
            },
            
            # Weekend events
            {
                'title': 'Shark Feeding Behind the Scenes',
                'description': 'Go behind the scenes to watch shark feeding time and learn about shark behavior.',
                'venue_idx': 1,  # Aquarium
                'is_interesting': True,
                'is_off_beat': True,
                'start_date': date.today() + timedelta(days=3),
                'start_time': time(16, 0),
                'duration_hours': 1.0,
                'cost': '$40',
                'registration_required': True,
                'max_participants': 8,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['behind-scenes', 'marine-life', 'exclusive', 'educational']
            },
            {
                'title': 'Victorian Mourning Jewelry Workshop',
                'description': 'Learn to create hair jewelry and mourning accessories in the Victorian tradition.',
                'venue_idx': 3,  # Library
                'is_off_beat': True,
                'is_interesting': True,
                'start_date': date.today() + timedelta(days=4),
                'start_time': time(13, 0),
                'duration_hours': 3.0,
                'cost': '$65',
                'registration_required': True,
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['historical', 'unusual', 'hands-on', 'cultural']
            },
            {
                'title': 'Boston Tea Party Reenactment & Debate',
                'description': 'Participate in a historical reenactment and debate the issues that led to the Tea Party.',
                'venue_idx': 0,  # Museum of Science
                'is_fun': True,
                'is_interesting': True,
                'start_date': date.today() + timedelta(days=5),
                'start_time': time(14, 0),
                'duration_hours': 2.5,
                'cost': '$35',
                'wheelchair_accessible': True,
                'indoor_outdoor': 'Indoor',
                'experience_tags': ['historical', 'interactive', 'educational', 'roleplay']
            }
        ]
        
        # Create events
        events_created = 0
        for event_data in boston_events:
            venue = created_venues[event_data['venue_idx']]
            
            event = Event(
                title=event_data['title'],
                venue_id=venue.id,
                start_date=event_data['start_date'],
                description=event_data.get('description'),
                start_time=event_data.get('start_time'),
                duration_hours=event_data.get('duration_hours'),
                is_fun=event_data.get('is_fun', False),
                is_interesting=event_data.get('is_interesting', False),
                is_off_beat=event_data.get('is_off_beat', False),
                cost=event_data.get('cost'),
                registration_required=event_data.get('registration_required', False),
                wheelchair_accessible=event_data.get('wheelchair_accessible', venue.wheelchair_accessible),
                indoor_outdoor=event_data.get('indoor_outdoor'),
                experience_tags=event_data.get('experience_tags', []),
                max_participants=event_data.get('max_participants')
            )
            
            # Update scores
            event.update_scores()
            
            db.session.add(event)
            events_created += 1
            
            print(f"Created event: {event.title} at {venue.name}")
        
        db.session.commit()
        
        print(f"\n✅ Successfully created {len(created_venues)} venues and {events_created} Boston-area events!")
        
        # Show today's events
        todays_events = Event.query.filter(Event.start_date == date.today()).all()
        print(f"\nToday's events ({len(todays_events)}):")
        for event in todays_events:
            types = ", ".join(event.get_event_types())
            print(f"  {event.title} - {types} at {event.venue.name}")

if __name__ == "__main__":
    create_boston_venues_and_events()