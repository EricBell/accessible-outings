"""
Base Event Provider - Abstract base class for event API integrations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class EventData:
    """Standardized event data structure for all providers"""
    title: str
    description: str
    start_date: date
    start_time: Optional[str]
    end_date: Optional[date]
    end_time: Optional[str]
    venue_name: str
    venue_address: str
    venue_latitude: Optional[float]
    venue_longitude: Optional[float]
    cost: Optional[float]
    registration_url: Optional[str]
    external_id: str
    source: str
    accessibility_info: Optional[str]
    category: Optional[str]
    organizer: Optional[str]
    max_participants: Optional[int]
    raw_data: Dict  # Store original API response


class BaseEventProvider(ABC):
    """Abstract base class for event providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.provider_name = self.get_provider_name()
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of this provider (e.g., 'eventbrite', 'meetup')"""
        pass
    
    @abstractmethod
    def search_events(
        self,
        location: str,
        start_date: date,
        end_date: date,
        category: Optional[str] = None,
        radius_miles: int = 25,
        max_results: int = 50
    ) -> List[EventData]:
        """
        Search for events in the specified location and date range
        
        Args:
            location: ZIP code, city, or coordinates
            start_date: Start of date range
            end_date: End of date range
            category: Event category filter
            radius_miles: Search radius in miles
            max_results: Maximum number of events to return
            
        Returns:
            List of EventData objects
        """
        pass
    
    @abstractmethod
    def get_event_details(self, external_id: str) -> Optional[EventData]:
        """Get detailed information for a specific event"""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate that the API key is working"""
        pass
    
    def extract_accessibility_info(self, description: str, venue_info: str = "") -> Optional[str]:
        """
        Extract accessibility information from event description and venue info
        This is a basic implementation - can be overridden by specific providers
        """
        accessibility_keywords = [
            'wheelchair accessible', 'wheelchair access', 'ada compliant',
            'accessible parking', 'accessible restroom', 'elevator access',
            'hearing loop', 'sign language', 'asl interpreter',
            'braille', 'large print', 'audio description',
            'mobility assistance', 'accessible entrance'
        ]
        
        text = f"{description} {venue_info}".lower()
        found_features = []
        
        for keyword in accessibility_keywords:
            if keyword in text:
                found_features.append(keyword)
        
        return "; ".join(found_features) if found_features else None
    
    def standardize_category(self, provider_category: str) -> str:
        """
        Map provider-specific categories to our standard categories
        Override this method in specific providers
        """
        category_mapping = {
            'arts': 'Art Galleries',
            'music': 'Theaters',
            'education': 'Libraries',
            'health': 'Museums',
            'business': 'Museums',
            'community': 'Museums',
            'sports': 'Museums',
            'food': 'Museums',
            'charity': 'Museums'
        }
        
        return category_mapping.get(provider_category.lower(), 'Museums')
    
    def validate_event_data(self, event_data: EventData) -> bool:
        """Validate that event data meets minimum requirements"""
        if not event_data.title or not event_data.start_date:
            return False
        
        if not event_data.venue_name and not event_data.venue_address:
            return False
        
        # Check if event is in the future
        if event_data.start_date < date.today():
            return False
        
        return True