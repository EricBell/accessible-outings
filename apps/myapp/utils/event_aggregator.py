"""
Event Aggregator - Combines events from multiple sources and manages the Event database
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, date
from flask import current_app

from models.event import Event
from models.venue import Venue
from models import db
from utils.event_integrations import EventbriteProvider, EventData


class EventAggregator:
    """Manages event data from multiple sources and syncs with database"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available event providers based on configuration"""
        # Initialize Eventbrite if API key is available
        eventbrite_key = current_app.config.get('EVENTBRITE_API_KEY')
        if eventbrite_key:
            try:
                provider = EventbriteProvider(eventbrite_key)
                if provider.validate_api_key():
                    self.providers.append(provider)
                    self.logger.info("Eventbrite provider initialized successfully")
                else:
                    self.logger.warning("Invalid Eventbrite API key")
            except Exception as e:
                self.logger.error(f"Failed to initialize Eventbrite provider: {e}")
        else:
            self.logger.info("No Eventbrite API key configured")
    
    def search_and_sync_events(
        self,
        location: str,
        start_date: date,
        end_date: date,
        event_types: List[str] = None,
        venue_ids: List[int] = None,
        max_results: int = 50
    ) -> List[Event]:
        """
        Search for events from external APIs and sync with database
        
        Args:
            location: ZIP code or city to search
            start_date: Start date for event search
            end_date: End date for event search
            event_types: List of event types to filter by
            venue_ids: List of venue IDs to filter by (optional)
            max_results: Maximum number of events to return
            
        Returns:
            List of Event objects from database
        """
        all_events = []
        
        # First, check existing events in database
        existing_events = Event.search_events(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            venue_ids=venue_ids
        )
        
        self.logger.info(f"Found {len(existing_events)} existing events in database")
        
        # If we have few events, search external sources
        if len(existing_events) < max_results // 2:
            self.logger.info(f"Searching external sources for more events near {location}")
            
            for provider in self.providers:
                try:
                    # Search this provider
                    provider_events = provider.search_events(
                        location=location,
                        start_date=start_date,
                        end_date=end_date,
                        max_results=max_results
                    )
                    
                    self.logger.info(f"Found {len(provider_events)} events from {provider.provider_name}")
                    
                    # Sync events to database
                    synced_events = self._sync_events_to_database(provider_events)
                    all_events.extend(synced_events)
                    
                except Exception as e:
                    self.logger.error(f"Error searching {provider.provider_name}: {e}")
                    continue
        
        # Combine existing and new events
        all_event_ids = set(e.id for e in existing_events)
        for event in all_events:
            if event.id not in all_event_ids:
                existing_events.append(event)
                all_event_ids.add(event.id)
        
        # Apply filters
        filtered_events = self._apply_filters(
            existing_events,
            event_types=event_types,
            venue_ids=venue_ids
        )
        
        # Limit results
        return filtered_events[:max_results]
    
    def _sync_events_to_database(self, event_data_list: List[EventData]) -> List[Event]:
        """Sync EventData objects to database Event objects"""
        synced_events = []
        
        for event_data in event_data_list:
            try:
                # Check if event already exists
                existing_event = Event.query.filter_by(
                    external_event_id=event_data.external_id,
                    source_api=event_data.source
                ).first()
                
                if existing_event:
                    # Update existing event
                    event = self._update_event_from_api_data(existing_event, event_data)
                else:
                    # Create new event
                    event = self._create_event_from_api_data(event_data)
                
                if event:
                    synced_events.append(event)
                    
            except Exception as e:
                self.logger.error(f"Failed to sync event {event_data.external_id}: {e}")
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            self.logger.info(f"Successfully synced {len(synced_events)} events to database")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to commit events to database: {e}")
            return []
        
        return synced_events
    
    def _create_event_from_api_data(self, event_data: EventData) -> Optional[Event]:
        """Create new Event object from EventData"""
        try:
            # Find or create venue
            venue = self._find_or_create_venue(event_data)
            if not venue:
                self.logger.warning(f"Could not find/create venue for event {event_data.title}")
                return None
            
            # Create event
            event = Event(
                title=event_data.title,
                venue_id=venue.id,
                start_date=event_data.start_date,
                start_time=datetime.strptime(event_data.start_time, '%H:%M').time() if event_data.start_time else None,
                end_date=event_data.end_date,
                end_time=datetime.strptime(event_data.end_time, '%H:%M').time() if event_data.end_time else None,
                description=event_data.description,
                cost=str(event_data.cost) if event_data.cost is not None else 'Check website',
                registration_url=event_data.registration_url,
                max_participants=event_data.max_participants,
                wheelchair_accessible=venue.wheelchair_accessible,  # Inherit from venue
                accessibility_notes=event_data.accessibility_info,
                source=event_data.source,
                source_api=event_data.source,
                external_event_id=event_data.external_id,
                last_verified=datetime.utcnow(),
                verification_status='verified',
                api_data=event_data.raw_data
            )
            
            # Set event type flags based on category and description
            self._set_event_types(event, event_data)
            
            db.session.add(event)
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to create event from API data: {e}")
            return None
    
    def _update_event_from_api_data(self, event: Event, event_data: EventData) -> Event:
        """Update existing Event with fresh API data"""
        try:
            # Update key fields
            event.title = event_data.title
            event.description = event_data.description
            event.cost = str(event_data.cost) if event_data.cost is not None else 'Check website'
            event.registration_url = event_data.registration_url
            event.max_participants = event_data.max_participants
            event.accessibility_notes = event_data.accessibility_info
            event.last_verified = datetime.utcnow()
            event.verification_status = 'verified'
            event.api_data = event_data.raw_data
            
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to update event {event.id}: {e}")
            return event
    
    def _find_or_create_venue(self, event_data: EventData) -> Optional[Venue]:
        """Find existing venue or create new one from event data"""
        try:
            # Try to find existing venue by name and location
            venue = Venue.query.filter_by(name=event_data.venue_name).first()
            
            if venue:
                # Update venue coordinates if we have better data
                if event_data.venue_latitude and event_data.venue_longitude:
                    if not venue.latitude or not venue.longitude:
                        venue.latitude = event_data.venue_latitude
                        venue.longitude = event_data.venue_longitude
                return venue
            
            # Create new venue
            venue = Venue(
                name=event_data.venue_name,
                address=event_data.venue_address,
                latitude=event_data.venue_latitude,
                longitude=event_data.venue_longitude,
                category_id=1,  # Default to Museums category
                wheelchair_accessible=True,  # Default to accessible
                source='api_event_venue'
            )
            
            db.session.add(venue)
            return venue
            
        except Exception as e:
            self.logger.error(f"Failed to find/create venue: {e}")
            return None
    
    def _set_event_types(self, event: Event, event_data: EventData):
        """Set event type flags based on content analysis"""
        title_lower = event_data.title.lower()
        desc_lower = (event_data.description or '').lower()
        text = f"{title_lower} {desc_lower}"
        
        # Fun keywords
        fun_keywords = [
            'workshop', 'class', 'painting', 'craft', 'art', 'music', 'dance',
            'cooking', 'game', 'party', 'festival', 'hands-on', 'interactive'
        ]
        
        # Interesting keywords
        interesting_keywords = [
            'lecture', 'talk', 'presentation', 'history', 'science', 'education',
            'learning', 'seminar', 'conference', 'discussion', 'tour', 'exhibit'
        ]
        
        # Off-beat keywords
        offbeat_keywords = [
            'unusual', 'unique', 'mystery', 'ghost', 'secret', 'behind-the-scenes',
            'exclusive', 'rare', 'underground', 'hidden', 'weird', 'strange'
        ]
        
        # Set flags based on keyword matches
        event.is_fun = any(keyword in text for keyword in fun_keywords)
        event.is_interesting = any(keyword in text for keyword in interesting_keywords)
        event.is_off_beat = any(keyword in text for keyword in offbeat_keywords)
        
        # Default to interesting if no other flags set
        if not (event.is_fun or event.is_interesting or event.is_off_beat):
            event.is_interesting = True
    
    def _apply_filters(
        self,
        events: List[Event],
        event_types: List[str] = None,
        venue_ids: List[int] = None
    ) -> List[Event]:
        """Apply additional filters to event list"""
        filtered_events = events
        
        # Filter by event types
        if event_types:
            filtered_events = []
            for event in events:
                if ('fun' in event_types and event.is_fun) or \
                   ('interesting' in event_types and event.is_interesting) or \
                   ('off_beat' in event_types and event.is_off_beat):
                    filtered_events.append(event)
        
        # Filter by venue IDs
        if venue_ids:
            filtered_events = [e for e in filtered_events if e.venue_id in venue_ids]
        
        return filtered_events
    
    def get_provider_status(self) -> Dict:
        """Get status of all event providers"""
        status = {}
        for provider in self.providers:
            status[provider.provider_name] = {
                'active': True,
                'api_key_valid': provider.validate_api_key()
            }
        return status