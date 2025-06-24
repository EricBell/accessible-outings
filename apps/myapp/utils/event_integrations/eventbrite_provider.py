"""
Eventbrite API Provider - Integration with Eventbrite Events API
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, date, time
from urllib.parse import urlencode
import logging

from .base_event_provider import BaseEventProvider, EventData


class EventbriteProvider(BaseEventProvider):
    """Eventbrite API integration for real event data"""
    
    BASE_URL = "https://www.eventbriteapi.com/v3"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_provider_name(self) -> str:
        return "eventbrite"
    
    def search_events(
        self,
        location: str,
        start_date: date,
        end_date: date,
        category: Optional[str] = None,
        radius_miles: int = 25,
        max_results: int = 50
    ) -> List[EventData]:
        """Search for events using Eventbrite API"""
        try:
            # Build search parameters
            params = {
                'location.address': location,
                'start_date.range_start': f"{start_date}T00:00:00",
                'start_date.range_end': f"{end_date}T23:59:59",
                'location.within': f"{radius_miles}mi",
                'sort_by': 'date',
                'expand': 'venue,organizer,category',
                'page_size': min(max_results, 50)  # Eventbrite max is 50 per page
            }
            
            # Add category filter if specified
            if category:
                eventbrite_category = self._map_category_to_eventbrite(category)
                if eventbrite_category:
                    params['categories'] = eventbrite_category
            
            # Make API request
            url = f"{self.BASE_URL}/events/search/"
            self.logger.info(f"Searching Eventbrite: {location}, {start_date} to {end_date}")
            
            response = self.session.get(url, params=params)
            
            # Check for specific error responses
            if response.status_code == 404:
                self.logger.error(f"Eventbrite API endpoint not found. Check API key and endpoint URL.")
                return []
            elif response.status_code == 401:
                self.logger.error(f"Eventbrite API authentication failed. Check API key.")
                return []
            
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            for event_data in data.get('events', []):
                try:
                    event = self._parse_event(event_data)
                    if event and self.validate_event_data(event):
                        events.append(event)
                except Exception as e:
                    self.logger.warning(f"Failed to parse event {event_data.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Found {len(events)} valid events from Eventbrite")
            return events
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Eventbrite API request failed: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Eventbrite search failed: {e}")
            return []
    
    def get_event_details(self, external_id: str) -> Optional[EventData]:
        """Get detailed information for a specific Eventbrite event"""
        try:
            url = f"{self.BASE_URL}/events/{external_id}/"
            params = {'expand': 'venue,organizer,category,description'}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            event_data = response.json()
            return self._parse_event(event_data)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get Eventbrite event {external_id}: {e}")
            return None
    
    def validate_api_key(self) -> bool:
        """Validate Eventbrite API key by making a test request"""
        try:
            url = f"{self.BASE_URL}/users/me/"
            response = self.session.get(url)
            if response.status_code == 200:
                self.logger.info("Eventbrite API key validation successful")
                return True
            else:
                self.logger.error(f"Eventbrite API key validation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Eventbrite API key validation error: {e}")
            return False
    
    def _parse_event(self, event_data: Dict) -> Optional[EventData]:
        """Parse Eventbrite event data into our standardized format"""
        try:
            # Extract basic event info
            title = event_data.get('name', {}).get('text', '').strip()
            description = event_data.get('description', {}).get('text', '') or ''
            
            # Parse dates and times
            start_datetime = self._parse_datetime(event_data.get('start', {}))
            end_datetime = self._parse_datetime(event_data.get('end', {}))
            
            if not start_datetime:
                return None
            
            # Extract venue information
            venue_data = event_data.get('venue') or {}
            venue_name = venue_data.get('name', 'Online Event')
            venue_address = self._format_venue_address(venue_data.get('address', {}))
            venue_lat = venue_data.get('latitude')
            venue_lon = venue_data.get('longitude')
            
            # Convert coordinates to float if they exist
            if venue_lat:
                venue_lat = float(venue_lat)
            if venue_lon:
                venue_lon = float(venue_lon)
            
            # Extract cost information
            cost = self._extract_cost(event_data)
            
            # Extract category
            category_data = event_data.get('category')
            category = None
            if category_data:
                category = self.standardize_category(category_data.get('short_name', ''))
            
            # Extract organizer
            organizer_data = event_data.get('organizer')
            organizer = organizer_data.get('name') if organizer_data else None
            
            # Extract accessibility info
            accessibility_info = self.extract_accessibility_info(
                description, 
                venue_address
            )
            
            # Build registration URL
            registration_url = event_data.get('url')
            
            # Extract capacity
            capacity = event_data.get('capacity')
            max_participants = int(capacity) if capacity and capacity.isdigit() else None
            
            return EventData(
                title=title,
                description=description[:1000],  # Limit description length
                start_date=start_datetime.date(),
                start_time=start_datetime.strftime('%H:%M') if start_datetime else None,
                end_date=end_datetime.date() if end_datetime else None,
                end_time=end_datetime.strftime('%H:%M') if end_datetime else None,
                venue_name=venue_name,
                venue_address=venue_address,
                venue_latitude=venue_lat,
                venue_longitude=venue_lon,
                cost=cost,
                registration_url=registration_url,
                external_id=event_data.get('id'),
                source='eventbrite',
                accessibility_info=accessibility_info,
                category=category,
                organizer=organizer,
                max_participants=max_participants,
                raw_data=event_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Eventbrite event: {e}")
            return None
    
    def _parse_datetime(self, datetime_data: Dict) -> Optional[datetime]:
        """Parse Eventbrite datetime format"""
        try:
            utc_time = datetime_data.get('utc')
            if utc_time:
                return datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
            
            local_time = datetime_data.get('local')
            if local_time:
                return datetime.fromisoformat(local_time)
            
            return None
        except:
            return None
    
    def _format_venue_address(self, address_data: Dict) -> str:
        """Format venue address from Eventbrite data"""
        if not address_data:
            return ""
        
        parts = []
        if address_data.get('address_1'):
            parts.append(address_data['address_1'])
        if address_data.get('city'):
            parts.append(address_data['city'])
        if address_data.get('region'):
            parts.append(address_data['region'])
        if address_data.get('postal_code'):
            parts.append(address_data['postal_code'])
        
        return ', '.join(parts)
    
    def _extract_cost(self, event_data: Dict) -> Optional[float]:
        """Extract cost information from Eventbrite event"""
        try:
            # Check if event is free
            if event_data.get('is_free', False):
                return 0.0
            
            # Try to get ticket price from ticket classes
            # This would require additional API call in real implementation
            # For now, return None to indicate price needs to be checked
            return None
            
        except:
            return None
    
    def _map_category_to_eventbrite(self, our_category: str) -> Optional[str]:
        """Map our categories to Eventbrite category IDs"""
        # Eventbrite category mapping
        # These are actual Eventbrite category IDs - you may need to adjust
        category_mapping = {
            'Art Galleries': '105',  # Arts
            'Museums': '103',        # Business & Professional
            'Libraries': '102',      # Education
            'Theaters': '105',       # Arts
            'Music': '105',          # Arts
            'Workshops': '102',      # Education
            'Classes': '102',        # Education
            'Tours': '110',          # Travel & Outdoor
            'Health': '107',         # Health & Wellness
            'Community': '113'       # Community & Culture
        }
        
        return category_mapping.get(our_category)
    
    def standardize_category(self, eventbrite_category: str) -> str:
        """Map Eventbrite categories to our standard categories"""
        category_mapping = {
            'arts': 'Art Galleries',
            'music': 'Theaters', 
            'education': 'Libraries',
            'business': 'Museums',
            'health': 'Museums',
            'community': 'Museums',
            'travel': 'Museums',
            'technology': 'Museums',
            'sports': 'Museums',
            'food': 'Museums',
            'charity': 'Museums',
            'religion': 'Museums',
            'family': 'Museums',
            'seasonal': 'Museums',
            'government': 'Museums',
            'other': 'Museums'
        }
        
        return category_mapping.get(eventbrite_category.lower(), 'Museums')