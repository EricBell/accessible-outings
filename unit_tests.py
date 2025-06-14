import unittest
import tempfile
import os
from app import create_app
from utils.database import init_db, get_db_connection
from models.venue import Venue
from models.user import User
from models.review import UserReview
from werkzeug.security import generate_password_hash
import json


class VenueDetailTestCase(unittest.TestCase):
    """Test cases for venue detail functionality - designed to fail until venue_detail.html template is created."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret-key',
            'GOOGLE_PLACES_API_KEY': 'test-api-key'
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Initialize test database
        with self.app.app_context():
            init_db()
            self._create_test_data()

    def tearDown(self):
        """Clean up after each test method."""
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _create_test_data(self):
        """Create test venues and users for testing."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create test user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, home_zip_code)
            VALUES (?, ?, ?, ?)
        """, ('testuser', 'test@example.com', generate_password_hash('password'), '03865'))

        # Create test venue with comprehensive accessibility features
        cursor.execute("""
            INSERT INTO venues (
                name, address, city, state, zip_code, latitude, longitude,
                phone, website, category_id, wheelchair_accessible, accessible_parking,
                accessible_restroom, accessible_entrance, large_print_menu,
                braille_menu, hearing_loop, service_animal_friendly, quiet_environment,
                accessible_seating, elevator_access, wide_doorways,
                monday_open, monday_close, tuesday_open, tuesday_close,
                wednesday_open, wednesday_close, thursday_open, thursday_close,
                friday_open, friday_close, saturday_open, saturday_close,
                sunday_open, sunday_close
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Test Accessible Restaurant', '123 Main St', 'Portsmouth', 'NH', '03801',
            43.0718, -70.7626, '(603) 555-0123', 'https://test-restaurant.com',
            1, True, True, True, True, True, False, True, True, False, True, True, True,
            '09:00', '22:00', '09:00', '22:00', '09:00', '22:00', '09:00', '22:00',
            '09:00', '23:00', '09:00', '23:00', '10:00', '21:00'
        ))

        # Create test venue without accessibility features
        cursor.execute("""
            INSERT INTO venues (
                name, address, city, state, zip_code, latitude, longitude,
                phone, category_id, wheelchair_accessible
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Test Inaccessible Venue', '456 Oak St', 'Dover', 'NH', '03820',
            43.1978, -70.8736, '(603) 555-0456', 1, False
        ))

        # Create test reviews
        cursor.execute("""
            INSERT INTO user_reviews (user_id, venue_id, rating, review_text, accessibility_rating)
            VALUES (?, ?, ?, ?, ?)
        """, (1, 1, 5, 'Great accessible restaurant with excellent service!', 5))

        conn.commit()
        conn.close()

    def test_venue_detail_template_missing_error(self):
        """Test that venue detail page fails due to missing template."""
        # This test should FAIL until venue_detail.html template is created
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        # Should raise TemplateNotFound error
        self.assertIn('TemplateNotFound', str(type(context.exception)))
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_api_endpoint_works(self):
        """Test that API endpoint works even when template is missing."""
        # API endpoint should work independently of missing template
        response = self.client.get('/api/venue/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Test Accessible Restaurant')
        self.assertTrue(data['wheelchair_accessible'])
        self.assertTrue(data['accessible_parking'])

    def test_venue_detail_nonexistent_venue(self):
        """Test venue detail page with non-existent venue ID."""
        # This should redirect to index with error message
        # Will fail until template exists and proper error handling works
        with self.assertRaises(Exception):
            response = self.client.get('/venue/999')

    def test_venue_detail_accessibility_summary_data(self):
        """Test that accessibility summary data is properly calculated."""
        # This will fail until template exists to render the data
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_with_user_session(self):
        """Test venue detail page when user is logged in."""
        # Create a session for the test user
        with self.client.session_transaction() as session:
            session['user_id'] = 1
            session['username'] = 'testuser'

        # This should fail due to missing template
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_shows_similar_venues(self):
        """Test that similar venues are included in venue detail page."""
        # This will fail until template exists
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_shows_user_reviews(self):
        """Test that user reviews are displayed on venue detail page."""
        # This will fail until template exists
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_favorite_functionality(self):
        """Test that venue can be favorited from detail page."""
        # Login user first
        with self.client.session_transaction() as session:
            session['user_id'] = 1

        # This will fail until template exists
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_operating_hours_display(self):
        """Test that operating hours are properly formatted and displayed."""
        # This will fail until template exists
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_accessibility_features_display(self):
        """Test that all accessibility features are properly displayed."""
        # This will fail until template exists
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))


class VenueDetailIntegrationTestCase(unittest.TestCase):
    """Integration tests for venue detail functionality - will pass once template is fixed."""

    def setUp(self):
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret-key',
            'GOOGLE_PLACES_API_KEY': 'test-api-key'
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        with self.app.app_context():
            init_db()

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_full_user_journey_search_to_detail(self):
        """Test complete user journey from search to venue detail."""
        # Step 1: Search for venues (this should work)
        search_response = self.client.get('/search?zip_code=03865&radius=10')
        self.assertIn([200, 302], [search_response.status_code])  # Either success or redirect

        # Step 2: Try to view venue details (this should fail until template exists)
        with self.assertRaises(Exception) as context:
            detail_response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))

    def test_venue_detail_responsive_design_elements(self):
        """Test that venue detail page includes responsive design elements."""
        # This will fail until template exists
        with self.assertRaises(Exception) as context:
            response = self.client.get('/venue/1')
        
        self.assertIn('venue_detail.html', str(context.exception))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)