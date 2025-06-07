import requests
import re
import logging
from typing import Optional, Tuple
from models.review import ApiCache

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for converting ZIP codes and addresses to coordinates."""
    
    def __init__(self, google_api_key: str):
        """Initialize the geocoding service."""
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.session = requests.Session()
    
    def _make_request(self, params: dict, cache_key: str = None) -> Optional[dict]:
        """Make a request to the Google Geocoding API with caching."""
        # Check cache first
        if cache_key:
            cached_data = ApiCache.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Using cached geocoding data for {cache_key}")
                return cached_data
        
        # Add API key to parameters
        params['key'] = self.google_api_key
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response if cache_key provided and request was successful
            if cache_key and data.get('status') == 'OK':
                # Cache geocoding data for 30 days since ZIP codes don't change
                ApiCache.set_cached_data(cache_key, data, ttl_hours=720)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse geocoding API response: {e}")
            return None
    
    def validate_zip_code(self, zip_code: str) -> bool:
        """Validate ZIP code format."""
        if not zip_code:
            return False
        
        # Remove any whitespace
        zip_code = zip_code.strip()
        
        # US ZIP code patterns
        # 5 digits: 12345
        # 5+4 digits: 12345-6789
        zip_patterns = [
            r'^\d{5}$',           # 5 digits
            r'^\d{5}-\d{4}$',     # 5+4 with dash
            r'^\d{9}$'            # 9 digits without dash
        ]
        
        return any(re.match(pattern, zip_code) for pattern in zip_patterns)
    
    def normalize_zip_code(self, zip_code: str) -> str:
        """Normalize ZIP code to standard 5-digit format."""
        if not zip_code:
            return ""
        
        # Remove whitespace and convert to string
        zip_code = str(zip_code).strip()
        
        # Extract just the first 5 digits
        digits = re.findall(r'\d', zip_code)
        if len(digits) >= 5:
            return ''.join(digits[:5])
        
        return zip_code
    
    def geocode_zip_code(self, zip_code: str) -> Optional[Tuple[float, float]]:
        """Convert ZIP code to latitude/longitude coordinates."""
        if not self.validate_zip_code(zip_code):
            logger.warning(f"Invalid ZIP code format: {zip_code}")
            return None
        
        normalized_zip = self.normalize_zip_code(zip_code)
        cache_key = f"geocode_zip_{normalized_zip}"
        
        params = {
            'address': normalized_zip,
            'components': 'country:US'  # Limit to US addresses
        }
        
        data = self._make_request(params, cache_key)
        
        if not data or data.get('status') != 'OK':
            logger.warning(f"Geocoding failed for ZIP {zip_code}: {data.get('status') if data else 'No response'}")
            return None
        
        results = data.get('results', [])
        if not results:
            logger.warning(f"No geocoding results for ZIP {zip_code}")
            return None
        
        # Get the first result
        result = results[0]
        geometry = result.get('geometry', {})
        location = geometry.get('location', {})
        
        latitude = location.get('lat')
        longitude = location.get('lng')
        
        if latitude is not None and longitude is not None:
            return float(latitude), float(longitude)
        
        logger.warning(f"Invalid coordinates in geocoding result for ZIP {zip_code}")
        return None
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to latitude/longitude coordinates."""
        if not address or not address.strip():
            return None
        
        address = address.strip()
        cache_key = f"geocode_address_{hash(address)}"
        
        params = {
            'address': address
        }
        
        data = self._make_request(params, cache_key)
        
        if not data or data.get('status') != 'OK':
            logger.warning(f"Geocoding failed for address '{address}': {data.get('status') if data else 'No response'}")
            return None
        
        results = data.get('results', [])
        if not results:
            logger.warning(f"No geocoding results for address '{address}'")
            return None
        
        # Get the first result
        result = results[0]
        geometry = result.get('geometry', {})
        location = geometry.get('location', {})
        
        latitude = location.get('lat')
        longitude = location.get('lng')
        
        if latitude is not None and longitude is not None:
            return float(latitude), float(longitude)
        
        logger.warning(f"Invalid coordinates in geocoding result for address '{address}'")
        return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[dict]:
        """Convert coordinates to address information."""
        cache_key = f"reverse_geocode_{latitude}_{longitude}"
        
        params = {
            'latlng': f"{latitude},{longitude}"
        }
        
        data = self._make_request(params, cache_key)
        
        if not data or data.get('status') != 'OK':
            logger.warning(f"Reverse geocoding failed for {latitude},{longitude}: {data.get('status') if data else 'No response'}")
            return None
        
        results = data.get('results', [])
        if not results:
            logger.warning(f"No reverse geocoding results for {latitude},{longitude}")
            return None
        
        # Parse the first result for address components
        result = results[0]
        address_components = result.get('address_components', [])
        
        address_info = {
            'formatted_address': result.get('formatted_address'),
            'street_number': None,
            'route': None,
            'locality': None,
            'administrative_area_level_1': None,
            'postal_code': None,
            'country': None
        }
        
        # Extract address components
        for component in address_components:
            types = component.get('types', [])
            long_name = component.get('long_name')
            short_name = component.get('short_name')
            
            if 'street_number' in types:
                address_info['street_number'] = long_name
            elif 'route' in types:
                address_info['route'] = long_name
            elif 'locality' in types:
                address_info['locality'] = long_name
            elif 'administrative_area_level_1' in types:
                address_info['administrative_area_level_1'] = short_name
            elif 'postal_code' in types:
                address_info['postal_code'] = long_name
            elif 'country' in types:
                address_info['country'] = short_name
        
        return address_info
    
    def get_zip_code_info(self, zip_code: str) -> Optional[dict]:
        """Get detailed information about a ZIP code."""
        coordinates = self.geocode_zip_code(zip_code)
        if not coordinates:
            return None
        
        latitude, longitude = coordinates
        address_info = self.reverse_geocode(latitude, longitude)
        
        if address_info:
            return {
                'zip_code': self.normalize_zip_code(zip_code),
                'latitude': latitude,
                'longitude': longitude,
                'city': address_info.get('locality'),
                'state': address_info.get('administrative_area_level_1'),
                'country': address_info.get('country'),
                'formatted_address': address_info.get('formatted_address')
            }
        
        return {
            'zip_code': self.normalize_zip_code(zip_code),
            'latitude': latitude,
            'longitude': longitude
        }
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula."""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        return c * r
    
    def is_within_radius(self, center_lat: float, center_lon: float, 
                        point_lat: float, point_lon: float, radius_miles: float) -> bool:
        """Check if a point is within a given radius of a center point."""
        distance = self.calculate_distance(center_lat, center_lon, point_lat, point_lon)
        return distance <= radius_miles

class LocationService:
    """High-level service for location-related operations."""
    
    def __init__(self, geocoding_service: GeocodingService):
        """Initialize the location service."""
        self.geocoding = geocoding_service
    
    def get_search_coordinates(self, zip_code: str = None, address: str = None, 
                             default_lat: float = None, default_lon: float = None) -> Optional[Tuple[float, float]]:
        """Get coordinates for search, trying multiple methods."""
        # Try ZIP code first
        if zip_code:
            coordinates = self.geocoding.geocode_zip_code(zip_code)
            if coordinates:
                return coordinates
        
        # Try address if ZIP code failed
        if address:
            coordinates = self.geocoding.geocode_address(address)
            if coordinates:
                return coordinates
        
        # Fall back to default coordinates
        if default_lat is not None and default_lon is not None:
            return default_lat, default_lon
        
        return None
    
    def validate_search_input(self, zip_code: str = None, address: str = None) -> dict:
        """Validate search input and return validation results."""
        result = {
            'valid': False,
            'zip_code_valid': False,
            'address_valid': False,
            'errors': []
        }
        
        if zip_code:
            if self.geocoding.validate_zip_code(zip_code):
                result['zip_code_valid'] = True
                result['valid'] = True
            else:
                result['errors'].append("Invalid ZIP code format")
        
        if address and address.strip():
            result['address_valid'] = True
            if not result['valid']:
                result['valid'] = True
        
        if not zip_code and not (address and address.strip()):
            result['errors'].append("Please provide either a ZIP code or address")
        
        return result
    
    def get_location_display_name(self, latitude: float, longitude: float) -> str:
        """Get a human-readable location name for coordinates."""
        address_info = self.geocoding.reverse_geocode(latitude, longitude)
        
        if address_info:
            city = address_info.get('locality')
            state = address_info.get('administrative_area_level_1')
            
            if city and state:
                return f"{city}, {state}"
            elif city:
                return city
            elif state:
                return state
        
        return f"{latitude:.4f}, {longitude:.4f}"
    

def main():
    """Validate the api key can be retrieved."""
    from dotenv import load_dotenv
    load_dotenv()
    import os
    google_api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    print("google api key ", google_api_key)
    geocoding_service = GeocodingService(google_api_key=google_api_key)
    print("geo svc", geocoding_service)

# import unittest
# from unittest.mock import patch
# import os
# from utils import geocoding   
# class TestGeocodingMain(unittest.TestCase):
 

#     @patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "testkey"})
#     def test_main(self):
#         # Optionally, patch print to capture output
#         with patch("builtins.print") as mock_print:
#             geocoding.main()
#             # Check that the API key was printed
#             mock_print.assert_any_call("google api key  testkey")
#             # Check that the GeocodingService object was printed
#             self.assertTrue(any("geo svc" in str(call) for call in mock_print.call_args_list))

if __name__ == "__main__":
    main()
    
 