"""
Dynamic Event Generator for Real Venues

This module generates plausible events for venues discovered via Google Places API
when no real event data is available from external sources.
"""

import random
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional
from models.event import Event
from models.venue import Venue
from models import db
import logging

logger = logging.getLogger(__name__)

class EventGenerator:
    """Generates plausible events for venues based on their category and characteristics."""
    
    # Event templates by venue category
    EVENT_TEMPLATES = {
        1: {  # Botanical Gardens
            'fun': [
                {"title": "Spring Flower Photography Workshop", "duration": 2.0, "cost": "$15", "hands_on": True},
                {"title": "Garden Sketching & Watercolor Class", "duration": 3.0, "cost": "$25", "hands_on": True},
                {"title": "Children's Nature Scavenger Hunt", "duration": 1.5, "cost": "Free", "hands_on": True},
                {"title": "Butterfly Garden Walk & Craft", "duration": 2.0, "cost": "$12", "hands_on": True},
            ],
            'interesting': [
                {"title": "Plant Propagation Workshop", "duration": 2.5, "cost": "$20", "hands_on": True},
                {"title": "Native Plants & Ecosystems Tour", "duration": 1.5, "cost": "$10", "hands_on": False},
                {"title": "Medicinal Herbs of New England", "duration": 2.0, "cost": "$18", "hands_on": False},
                {"title": "Climate Change & Local Flora", "duration": 1.0, "cost": "Free", "hands_on": False},
            ],
            'off_beat': [
                {"title": "Midnight Garden: Plants That Bloom at Night", "duration": 1.5, "cost": "$25", "hands_on": False},
                {"title": "Carnivorous Plants: Nature's Predators", "duration": 2.0, "cost": "$22", "hands_on": True},
                {"title": "Garden Mysteries: Solving Plant Problems", "duration": 2.5, "cost": "$20", "hands_on": True},
            ]
        },
        3: {  # Museums
            'fun': [
                {"title": "Hands-On History: {venue_name} Workshop", "duration": 2.0, "cost": "$15", "hands_on": True},
                {"title": "Family Art-Making Session", "duration": 2.5, "cost": "$20", "hands_on": True},
                {"title": "Interactive Science Demonstration", "duration": 1.5, "cost": "$12", "hands_on": True},
                {"title": "Museum Treasure Hunt", "duration": 1.0, "cost": "Free", "hands_on": True},
            ],
            'interesting': [
                {"title": "Curator's Special Exhibition Tour", "duration": 1.5, "cost": "$18", "hands_on": False},
                {"title": "Behind the Scenes: Museum Conservation", "duration": 2.0, "cost": "$25", "hands_on": False},
                {"title": "Local History Lecture Series", "duration": 1.5, "cost": "$15", "hands_on": False},
                {"title": "Artist Talk & Gallery Discussion", "duration": 2.0, "cost": "$20", "hands_on": False},
            ],
            'off_beat': [
                {"title": "After Hours: Mysterious Collections", "duration": 2.0, "cost": "$30", "hands_on": False},
                {"title": "Secrets of the Storage Room Tour", "duration": 1.5, "cost": "$25", "hands_on": False},
                {"title": "Paranormal History: Haunted Artifacts", "duration": 2.5, "cost": "$35", "hands_on": False},
            ]
        },
        4: {  # Aquariums
            'fun': [
                {"title": "Touch Tank Experience & Marine Crafts", "duration": 2.0, "cost": "$18", "hands_on": True},
                {"title": "Fish Feeding Behind the Scenes", "duration": 1.5, "cost": "$25", "hands_on": True},
                {"title": "Ocean Animal Drawing Workshop", "duration": 2.5, "cost": "$20", "hands_on": True},
                {"title": "Build Your Own Coral Reef Model", "duration": 2.0, "cost": "$22", "hands_on": True},
            ],
            'interesting': [
                {"title": "Marine Biology Q&A with Aquarists", "duration": 1.5, "cost": "$15", "hands_on": False},
                {"title": "Ocean Conservation Workshop", "duration": 2.0, "cost": "$18", "hands_on": False},
                {"title": "Aquatic Ecosystem Science Talk", "duration": 1.0, "cost": "Free", "hands_on": False},
                {"title": "Dive Show: Professional Underwater Demo", "duration": 1.5, "cost": "$20", "hands_on": False},
            ],
            'off_beat': [
                {"title": "Night Shift: When Sea Creatures Wake Up", "duration": 2.0, "cost": "$35", "hands_on": False},
                {"title": "Mysterious Deep Sea Creatures Tour", "duration": 1.5, "cost": "$25", "hands_on": False},
                {"title": "Shark Encounter: Up Close & Personal", "duration": 2.0, "cost": "$40", "hands_on": True},
            ]
        },
        8: {  # Libraries
            'fun': [
                {"title": "Community Book Club Discussion", "duration": 2.0, "cost": "Free", "hands_on": False},
                {"title": "Storytelling & Craft Hour", "duration": 1.5, "cost": "Free", "hands_on": True},
                {"title": "Poetry Reading & Open Mic", "duration": 2.0, "cost": "Free", "hands_on": False},
                {"title": "Board Game Tournament", "duration": 3.0, "cost": "Free", "hands_on": True},
            ],
            'interesting': [
                {"title": "Local Author Reading & Q&A", "duration": 1.5, "cost": "Free", "hands_on": False},
                {"title": "Digital Literacy Workshop", "duration": 2.0, "cost": "Free", "hands_on": True},
                {"title": "Genealogy Research Class", "duration": 2.5, "cost": "Free", "hands_on": True},
                {"title": "Financial Planning Seminar", "duration": 2.0, "cost": "Free", "hands_on": False},
            ],
            'off_beat': [
                {"title": "Rare Books & Hidden Treasures Tour", "duration": 1.5, "cost": "Free", "hands_on": False},
                {"title": "Mystery Book Discussion: Unsolved Crimes", "duration": 2.0, "cost": "Free", "hands_on": False},
                {"title": "Silent Library Challenge", "duration": 1.0, "cost": "Free", "hands_on": True},
            ]
        },
        9: {  # Theaters
            'fun': [
                {"title": "Improv Comedy Workshop", "duration": 2.5, "cost": "$25", "hands_on": True},
                {"title": "Stage Makeup & Costume Workshop", "duration": 3.0, "cost": "$30", "hands_on": True},
                {"title": "Kids' Theater Camp Day", "duration": 4.0, "cost": "$35", "hands_on": True},
                {"title": "Community Sing-Along Night", "duration": 2.0, "cost": "$10", "hands_on": True},
            ],
            'interesting': [
                {"title": "Theater History & Architecture Tour", "duration": 1.5, "cost": "$15", "hands_on": False},
                {"title": "Backstage Technical Tour", "duration": 2.0, "cost": "$20", "hands_on": False},
                {"title": "Actor's Workshop: Method Acting", "duration": 3.0, "cost": "$40", "hands_on": True},
                {"title": "Playwright Reading & Discussion", "duration": 2.0, "cost": "$18", "hands_on": False},
            ],
            'off_beat': [
                {"title": "Ghost Light: Haunted Theater Stories", "duration": 1.5, "cost": "$25", "hands_on": False},
                {"title": "Midnight Rehearsal: Behind Closed Curtains", "duration": 2.5, "cost": "$35", "hands_on": False},
                {"title": "Theater Mysteries: Unsolved Backstage Stories", "duration": 2.0, "cost": "$30", "hands_on": False},
            ]
        },
        # Default category for unknown venues
        'default': {
            'fun': [
                {"title": "Community Workshop at {venue_name}", "duration": 2.0, "cost": "$20", "hands_on": True},
                {"title": "Hands-On Learning Experience", "duration": 2.5, "cost": "$25", "hands_on": True},
                {"title": "Family Activity Session", "duration": 1.5, "cost": "$15", "hands_on": True},
            ],
            'interesting': [
                {"title": "Educational Tour & Presentation", "duration": 1.5, "cost": "$15", "hands_on": False},
                {"title": "Expert-Led Discussion", "duration": 2.0, "cost": "$20", "hands_on": False},
                {"title": "Learning Workshop", "duration": 2.5, "cost": "$25", "hands_on": True},
            ],
            'off_beat': [
                {"title": "Hidden Secrets Behind the Scenes", "duration": 2.0, "cost": "$30", "hands_on": False},
                {"title": "Unique Experience at {venue_name}", "duration": 2.5, "cost": "$35", "hands_on": True},
            ]
        }
    }
    
    @classmethod
    def generate_events_for_venue(cls, venue: Venue, event_types: List[str] = None, 
                                  max_events: int = 3) -> List[Event]:
        """Generate plausible events for a venue based on its category and characteristics."""
        if not event_types:
            event_types = ['fun', 'interesting', 'off_beat']
        
        # Get category templates or use default
        category_templates = cls.EVENT_TEMPLATES.get(venue.category_id, cls.EVENT_TEMPLATES['default'])
        
        generated_events = []
        events_per_type = max(1, max_events // len(event_types))
        
        for event_type in event_types:
            if event_type not in category_templates:
                continue
                
            templates = category_templates[event_type]
            selected_templates = random.sample(templates, min(events_per_type, len(templates)))
            
            for template in selected_templates:
                event = cls._create_event_from_template(venue, template, event_type)
                if event:
                    generated_events.append(event)
                    
                if len(generated_events) >= max_events:
                    break
            
            if len(generated_events) >= max_events:
                break
        
        return generated_events
    
    @classmethod
    def _create_event_from_template(cls, venue: Venue, template: Dict, event_type: str) -> Optional[Event]:
        """Create an event from a template."""
        try:
            # Generate event dates (next 30 days)
            start_date = cls._generate_random_future_date()
            start_time = cls._generate_random_time(venue)
            
            # Format title with venue name if needed
            title = template['title'].format(venue_name=venue.name)
            
            # Create description
            description = cls._generate_description(venue, template, event_type)
            
            # Set event type flags
            is_fun = event_type == 'fun'
            is_interesting = event_type == 'interesting'
            is_off_beat = event_type == 'off_beat'
            
            # Create event
            event = Event(
                title=title,
                venue_id=venue.id,
                start_date=start_date,
                start_time=start_time,
                description=description,
                duration_hours=template.get('duration', 2.0),
                cost=template.get('cost', '$20'),
                is_fun=is_fun,
                is_interesting=is_interesting,
                is_off_beat=is_off_beat,
                wheelchair_accessible=venue.wheelchair_accessible,
                indoor_outdoor='Indoor',  # Assume most venue events are indoor
                registration_required=True,
                age_restriction='All ages',
                audience_type='General public',
                source='auto_generated',
                accessibility_notes=f"Event venue is {'wheelchair accessible' if venue.wheelchair_accessible else 'may have accessibility limitations'}."
            )
            
            # Set experience tags based on template
            if template.get('hands_on'):
                event.experience_tags = ['hands-on', 'interactive']
            else:
                event.experience_tags = ['educational', 'informative']
            
            # Update calculated scores
            event.update_scores()
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating event from template: {e}")
            return None
    
    @classmethod
    def _generate_random_future_date(cls, days_ahead: int = 30) -> date:
        """Generate a random date within the next N days."""
        today = date.today()
        random_days = random.randint(0, days_ahead)
        return today + timedelta(days=random_days)
    
    @classmethod
    def _generate_random_time(cls, venue: Venue) -> time:
        """Generate a reasonable time for an event based on venue type."""
        # Different venue types have different typical event times
        if venue.category_id == 8:  # Libraries - often have evening programs
            hours = random.choice([10, 14, 18, 19])
        elif venue.category_id == 9:  # Theaters - often evening events
            hours = random.choice([19, 20])
        elif venue.category_id in [3, 4]:  # Museums, Aquariums - daytime events
            hours = random.choice([10, 11, 13, 14, 15])
        else:  # General venues
            hours = random.choice([10, 11, 13, 14, 15, 18, 19])
        
        minutes = random.choice([0, 30])
        return time(hours, minutes)
    
    @classmethod
    def _generate_description(cls, venue: Venue, template: Dict, event_type: str) -> str:
        """Generate a description for the event."""
        base_descriptions = {
            'fun': f"Join us for an engaging and enjoyable experience at {venue.name}! This hands-on activity is perfect for all skill levels.",
            'interesting': f"Learn something new at {venue.name} with this educational and informative session led by knowledgeable staff.",
            'off_beat': f"Discover the unique and unusual side of {venue.name} in this special behind-the-scenes experience."
        }
        
        description = base_descriptions.get(event_type, f"Experience something special at {venue.name}!")
        
        # Add accessibility information
        if venue.wheelchair_accessible:
            description += " This venue is wheelchair accessible with ramps and accessible facilities."
        
        # Add practical information
        if template.get('hands_on'):
            description += " All materials and instruction will be provided."
        
        description += f" Duration: approximately {template.get('duration', 2.0)} hours."
        
        return description
    
    @classmethod
    def get_or_create_events_for_venues(cls, venues: List[Venue], event_types: List[str] = None) -> List[Event]:
        """Get existing events or generate new ones for a list of venues."""
        all_events = []
        venue_ids = [venue.id for venue in venues]
        
        # Get existing events for these venues
        existing_events = Event.query.filter(Event.venue_id.in_(venue_ids)).all()
        
        # Group existing events by venue
        events_by_venue = {}
        for event in existing_events:
            if event.venue_id not in events_by_venue:
                events_by_venue[event.venue_id] = []
            events_by_venue[event.venue_id].append(event)
        
        # Generate events for venues that don't have enough events
        for venue in venues:
            venue_events = events_by_venue.get(venue.id, [])
            
            # If venue has no events or very few, generate some
            if len(venue_events) < 2:
                new_events = cls.generate_events_for_venue(
                    venue, 
                    event_types=event_types, 
                    max_events=3 - len(venue_events)
                )
                
                # Add to database
                for event in new_events:
                    db.session.add(event)
                    venue_events.append(event)
                
                try:
                    db.session.commit()
                    logger.info(f"Generated {len(new_events)} events for venue: {venue.name}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to save generated events for {venue.name}: {e}")
            
            all_events.extend(venue_events)
        
        return all_events