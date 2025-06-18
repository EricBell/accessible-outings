import requests
import logging
from typing import List, Dict, Optional, Tuple
from models.review import ApiCache
from models.venue import Venue, VenueCategory
from models import db

logger = logging.getLogger(__name__)

class GooglePlacesAPI:
    """Google Places API integration for venue discovery."""
    
    def __init__(self, api_key: str):
        """Initialize the Google Places API client."""
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: dict, cache_key: str = None, 
                     cache_hours: int = 24) -> Optional[dict]:
        """Make a request to the Google Places API with caching."""
        # Check cache first
        if cache_key:
            cached_data = ApiCache.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Using cached data for {cache_key}")
                return cached_data
        
        # Add API key to parameters
        params['key'] = self.api_key
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response if cache_key provided
            if cache_key and data.get('status') == 'OK':
                ApiCache.set_cached_data(cache_key, data, cache_hours)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Places API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse Google Places API response: {e}")
            return None
    
    def search_nearby(self, latitude: float, longitude: float, radius: int = 30000,
                     venue_type: str = None, keyword: str = None) -> List[Dict]:
        """Search for venues near given coordinates."""
        params = {
            'location': f"{latitude},{longitude}",
            'radius': min(radius, 50000),  # Google Places API max radius
            'type': venue_type or 'establishment'
        }
        
        if keyword:
            params['keyword'] = keyword
        
        # Create cache key
        cache_key = f"nearby_{latitude}_{longitude}_{radius}_{venue_type}_{keyword}"
        
        data = self._make_request('nearbysearch/json', params, cache_key)
        
        if not data or data.get('status') != 'OK':
            logger.warning(f"Google Places nearby search failed: {data.get('status') if data else 'No response'}")
            return []
        
        return data.get('results', [])
    
    def text_search(self, query: str, location: str = None, radius: int = 30000) -> List[Dict]:
        """Search for venues using text query."""
        params = {
            'query': query,
            'type': 'establishment'
        }
        
        if location:
            params['location'] = location
            params['radius'] = radius
        
        # Create cache key
        cache_key = f"text_search_{hash(query)}_{location}_{radius}"
        
        data = self._make_request('textsearch/json', params, cache_key)
        
        if not data or data.get('status') != 'OK':
            logger.warning(f"Google Places text search failed: {data.get('status') if data else 'No response'}")
            return []
        
        return data.get('results', [])
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a specific place."""
        params = {
            'place_id': place_id,
            'fields': 'place_id,name,formatted_address,geometry,formatted_phone_number,'
                     'website,rating,price_level,opening_hours,photos,types,reviews,'
                     'wheelchair_accessible_entrance'
        }
        
        cache_key = f"place_details_{place_id}"
        
        data = self._make_request('details/json', params, cache_key, cache_hours=168)  # Cache for 1 week
        
        if not data or data.get('status') != 'OK':
            logger.warning(f"Google Places details failed: {data.get('status') if data else 'No response'}")
            return None
        
        return data.get('result')
    
    def search_by_category(self, latitude: float, longitude: float, 
                          category: VenueCategory, radius: int = 30000) -> List[Dict]:
        """Search for venues by category using keywords."""
        all_results = []
        
        # Use category keywords for search
        keywords = category.search_keywords or [category.name.lower()]
        
        for keyword in keywords[:3]:  # Limit to first 3 keywords to avoid too many API calls
            results = self.search_nearby(latitude, longitude, radius, keyword=keyword)
            
            # Filter out duplicates based on place_id
            existing_place_ids = {result.get('place_id') for result in all_results}
            new_results = [r for r in results if r.get('place_id') not in existing_place_ids]
            
            all_results.extend(new_results)
            
            # Limit total results to avoid overwhelming the user
            if len(all_results) >= 60:
                break
        
        return all_results[:60]  # Return max 60 results
    
    def extract_accessibility_info(self, place_data: Dict) -> Dict:
        """Extract accessibility information from Google Places data."""
        accessibility = {
            'wheelchair_accessible': False,
            'accessible_parking': False,
            'accessible_restroom': False,
            'elevator_access': False,
            'wide_doorways': False,
            'ramp_access': False,
            'accessible_seating': False,
            'accessibility_notes': ''
        }
        
        # Check for wheelchair accessible entrance
        if place_data.get('wheelchair_accessible_entrance'):
            accessibility['wheelchair_accessible'] = True
            accessibility['accessibility_notes'] += 'Wheelchair accessible entrance. '
        
        # Check reviews for accessibility mentions
        reviews = place_data.get('reviews', [])
        accessibility_keywords = {
            'wheelchair': ['wheelchair_accessible', 'ramp_access'],
            'accessible': ['wheelchair_accessible'],
            'ramp': ['ramp_access'],
            'elevator': ['elevator_access'],
            'parking': ['accessible_parking'],
            'restroom': ['accessible_restroom'],
            'bathroom': ['accessible_restroom'],
            'wide door': ['wide_doorways'],
            'accessible seating': ['accessible_seating']
        }
        
        accessibility_mentions = []
        for review in reviews[:5]:  # Check first 5 reviews
            review_text = review.get('text', '').lower()
            for keyword, features in accessibility_keywords.items():
                if keyword in review_text:
                    for feature in features:
                        accessibility[feature] = True
                    accessibility_mentions.append(f"Mentioned in reviews: {keyword}")
        
        if accessibility_mentions:
            accessibility['accessibility_notes'] += ' '.join(accessibility_mentions)
        
        return accessibility
    
    def convert_to_venue_data(self, place_data: Dict, category_id: int = None) -> Dict:
        """Convert Google Places data to venue data format."""
        geometry = place_data.get('geometry', {})
        location = geometry.get('location', {})
        
        # Extract address components
        address_components = place_data.get('formatted_address', '').split(', ')
        
        venue_data = {
            'google_place_id': place_data.get('place_id'),
            'name': place_data.get('name'),
            'address': address_components[0] if address_components else '',
            'latitude': location.get('lat'),
            'longitude': location.get('lng'),
            'phone': place_data.get('formatted_phone_number'),
            'website': place_data.get('website'),
            'google_rating': place_data.get('rating'),
            'price_level': place_data.get('price_level'),
            'category_id': category_id
        }
        
        # Parse address components
        if len(address_components) >= 3:
            # Extract state and zip from the component before last (usually "NH 03301")
            state_zip_part = address_components[-2]  # Usually "State ZIP"
            if ' ' in state_zip_part:
                parts = state_zip_part.split(' ')
                venue_data['state'] = parts[0]
                venue_data['zip_code'] = parts[1] if len(parts) > 1 else None
            
            # City is the component before state/zip (usually the actual city name)
            if len(address_components) >= 4:
                venue_data['city'] = address_components[-3]
            elif len(address_components) == 3:
                venue_data['city'] = address_components[1]
        
        # Extract operating hours
        opening_hours = place_data.get('opening_hours', {})
        if opening_hours.get('weekday_text'):
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for i, day_hours in enumerate(opening_hours['weekday_text']):
                if i < len(days):
                    # Remove day name from the beginning
                    hours = day_hours.split(': ', 1)[-1]
                    venue_data[f'hours_{days[i]}'] = hours
        
        # Extract photo URLs
        photos = place_data.get('photos', [])
        if photos:
            photo_urls = []
            for photo in photos[:5]:  # Limit to 5 photos
                photo_reference = photo.get('photo_reference')
                if photo_reference:
                    photo_url = f"{self.base_url}/photo?maxwidth=400&photoreference={photo_reference}&key={self.api_key}"
                    photo_urls.append(photo_url)
            venue_data['photo_urls'] = photo_urls
        
        # Extract accessibility information
        accessibility_info = self.extract_accessibility_info(place_data)
        venue_data.update(accessibility_info)
        
        return venue_data

class VenueSearchService:
    """Service for searching and managing venues using Google Places API."""
    
    def __init__(self, google_places_api: GooglePlacesAPI):
        """Initialize the venue search service."""
        self.google_api = google_places_api
    
    def search_venues(self, latitude: float, longitude: float, radius_miles: int = 30,
                     category_id: int = None, wheelchair_accessible_only: bool = False) -> List[Venue]:
        """Search for venues and return Venue objects."""
        radius_meters = int(radius_miles * 1609.34)  # Convert miles to meters
        
        # Get category if specified
        category = None
        if category_id:
            category = VenueCategory.query.get(category_id)
            if not category:
                logger.warning(f"Category {category_id} not found")
                return []
        
        # Search using Google Places API
        if category:
            places_data = self.google_api.search_by_category(latitude, longitude, category, radius_meters)
        else:
            places_data = self.google_api.search_nearby(latitude, longitude, radius_meters)
        
        venues = []
        for place_data in places_data:
            try:
                venue = self._process_place_data(place_data, category_id)
                if venue:
                    # Filter by accessibility if requested
                    if wheelchair_accessible_only and not venue.wheelchair_accessible:
                        continue
                    venues.append(venue)
            except Exception as e:
                logger.error(f"Error processing place data: {e}")
                continue
        
        # Sort by distance
        venues.sort(key=lambda v: v.distance_from(latitude, longitude) or float('inf'))
        
        return venues
    
    def _process_place_data(self, place_data: Dict, category_id: int = None) -> Optional[Venue]:
        """Process Google Places data and create/update venue."""
        place_id = place_data.get('place_id')
        if not place_id:
            return None
        
        # Check if venue already exists
        existing_venue = Venue.find_by_google_place_id(place_id)
        
        if existing_venue:
            # Update existing venue if it's old
            from datetime import datetime, timedelta
            if existing_venue.last_updated < datetime.utcnow() - timedelta(days=7):
                # Get fresh details from Google Places
                detailed_data = self.google_api.get_place_details(place_id)
                if detailed_data:
                    venue_data = self.google_api.convert_to_venue_data(detailed_data, category_id)
                    for key, value in venue_data.items():
                        if hasattr(existing_venue, key) and value is not None:
                            setattr(existing_venue, key, value)
                    existing_venue.last_updated = datetime.utcnow()
                    db.session.commit()
            return existing_venue
        
        # Create new venue
        # Get detailed information
        detailed_data = self.google_api.get_place_details(place_id)
        if not detailed_data:
            # Fall back to basic data
            detailed_data = place_data
        
        venue_data = self.google_api.convert_to_venue_data(detailed_data, category_id)
        
        # Create venue object
        venue = Venue(**venue_data)
        db.session.add(venue)
        
        try:
            db.session.commit()
            logger.info(f"Created new venue: {venue.name}")
            return venue
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create venue: {e}")
            return None
    
    def get_venue_details(self, venue_id: int) -> Optional[Venue]:
        """Get detailed venue information."""
        venue = Venue.query.get(venue_id)
        if not venue:
            return None
        
        # Refresh data if it's old
        from datetime import datetime, timedelta
        if venue.last_updated < datetime.utcnow() - timedelta(days=7):
            if venue.google_place_id:
                detailed_data = self.google_api.get_place_details(venue.google_place_id)
                if detailed_data:
                    venue_data = self.google_api.convert_to_venue_data(detailed_data, venue.category_id)
                    for key, value in venue_data.items():
                        if hasattr(venue, key) and value is not None:
                            setattr(venue, key, value)
                    venue.last_updated = datetime.utcnow()
                    db.session.commit()
        
        return venue
