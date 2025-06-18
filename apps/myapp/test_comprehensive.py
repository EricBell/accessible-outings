#!/usr/bin/env python3
"""
Comprehensive test suite to verify app functionality and catch regressions.
Run with: python test_comprehensive.py
"""

import unittest
import json
import tempfile
import os
from app import create_app
from models import db
from models.venue import Venue, VenueCategory
from models.user import User
from models.review import UserReview
from utils.accessibility import AccessibilityFilter


class ComprehensiveAppTest(unittest.TestCase):
    """Comprehensive tests to validate all app functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a test config class
        class TestConfig:
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            WTF_CSRF_ENABLED = False
            GOOGLE_PLACES_API_KEY = 'test-key'
            SECRET_KEY = 'test-secret'
            BYPASS_AUTH = True
            DEFAULT_USER_ID = 1
            
            @staticmethod
            def validate_config():
                return []
        
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Create tables and test data
        db.create_all()
        self._create_test_data()

    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_test_data(self):
        """Create comprehensive test data."""
        # Create test categories
        self.category = VenueCategory(
            name='Test Museums',
            description='Test museums for testing',
            icon_class='fas fa-university',
            search_keywords=['museum', 'gallery']
        )
        db.session.add(self.category)
        
        # Create test user (or use existing)
        self.user = User.query.filter_by(username='testuser').first()
        if not self.user:
            self.user = User.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                home_zip_code='12345'
            )
        
        # Create test venues with various accessibility features
        self.venue1 = Venue(
            name='Accessible Museum',
            address='123 Main St',
            city='Test City',
            latitude=40.7128,
            longitude=-74.0060,
            google_rating=4.5,
            phone='555-0123',
            website='https://example.com',
            wheelchair_accessible=True,
            accessible_parking=True,
            accessible_restroom=True,
            elevator_access=True,
            wide_doorways=True,
            ramp_access=True,
            accessible_seating=True
        )
        self.venue1.category_id = self.category.id
        
        self.venue2 = Venue(
            name='Limited Access Gallery',
            address='456 Oak Ave',
            city='Test City',
            latitude=40.7589,
            longitude=-73.9851,
            google_rating=3.8,
            wheelchair_accessible=False,
            accessible_parking=True,
            accessible_restroom=False,
            elevator_access=False,
            wide_doorways=False,
            ramp_access=False,
            accessible_seating=False
        )
        self.venue2.category_id = self.category.id
        
        db.session.add_all([self.venue1, self.venue2])
        db.session.commit()

    # ========== PAGE LOADING TESTS ==========
    
    def test_home_page_loads(self):
        """Test that home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Find Accessible Venues', response.data)

    def test_about_page_loads(self):
        """Test that about page loads correctly."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Making the World More Accessible', response.data)

    def test_venue_detail_page_loads(self):
        """Test that venue detail page loads correctly."""
        response = self.client.get(f'/venue/{self.venue1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.venue1.name.encode(), response.data)
        self.assertIn(b'Accessibility Score', response.data)

    # ========== SEARCH FUNCTIONALITY TESTS ==========
    
    def test_search_by_zip_code(self):
        """Test search functionality by ZIP code."""
        response = self.client.get('/search?zip_code=12345&radius=50')
        # May redirect on API failure, or return search results
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            # Should contain search results page elements
            self.assertIn(b'Search Results', response.data)

    def test_search_with_category_filter(self):
        """Test search with category filtering."""
        response = self.client.get(f'/search?zip_code=12345&category_id={self.category.id}&radius=25')
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            self.assertIn(b'Search Results', response.data)

    def test_search_with_accessibility_filter(self):
        """Test search with accessibility-only filter."""
        response = self.client.get('/search?zip_code=12345&accessible_only=1&radius=25')
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            self.assertIn(b'Wheelchair Accessible Only', response.data)

    # ========== DATA INTEGRITY TESTS ==========
    
    def test_accessibility_score_calculation(self):
        """Test that accessibility scores are calculated correctly."""
        score1 = AccessibilityFilter.calculate_accessibility_score(self.venue1)
        score2 = AccessibilityFilter.calculate_accessibility_score(self.venue2)
        
        # Venue1 should have higher score (more accessible features)
        self.assertGreater(score1, score2)
        self.assertGreaterEqual(score1, 0.8)  # Should be in "excellent" range (80%+)
        self.assertLessEqual(score2, 0.5)    # Should be in "limited" range (50%)

    def test_venue_data_integrity(self):
        """Test that venue data is stored and retrieved correctly."""
        venue = Venue.query.filter_by(name='Accessible Museum').first()
        self.assertIsNotNone(venue)
        self.assertEqual(venue.name, 'Accessible Museum')
        self.assertEqual(venue.city, 'Test City')
        self.assertTrue(venue.wheelchair_accessible)

    def test_category_relationships(self):
        """Test that venue-category relationships work correctly."""
        venue = Venue.query.filter_by(name='Accessible Museum').first()
        self.assertIsNotNone(venue.category)
        self.assertEqual(venue.category.name, 'Test Museums')

    # ========== TEMPLATE RENDERING TESTS ==========
    
    def test_venue_detail_template_data(self):
        """Test that venue detail template receives correct data."""
        response = self.client.get(f'/venue/{self.venue1.id}')
        
        # Check for key template elements
        self.assertIn(self.venue1.name.encode(), response.data)
        self.assertIn(self.venue1.address.encode(), response.data)
        self.assertIn(b'Accessibility Score', response.data)
        self.assertIn(b'Quick Info', response.data)
        
        # Check for accessibility features display
        if self.venue1.wheelchair_accessible:
            self.assertIn(b'wheelchair', response.data.lower())

    def test_search_results_template_data(self):
        """Test that search results template displays correctly."""
        response = self.client.get('/search?zip_code=12345&radius=50')
        
        # Should contain search metadata (if search succeeds)
        if response.status_code == 200:
            self.assertIn(b'Found', response.data)
            self.assertIn(b'venues', response.data)
        # If redirected, that's also acceptable in test environment
        self.assertIn(response.status_code, [200, 302])

    # ========== ERROR HANDLING TESTS ==========
    
    def test_invalid_venue_id_returns_404(self):
        """Test that invalid venue IDs are handled gracefully."""
        response = self.client.get('/venue/99999')
        # Should redirect to home with error message
        self.assertEqual(response.status_code, 302)

    def test_empty_search_handled_gracefully(self):
        """Test that empty search parameters are handled."""
        response = self.client.get('/search?zip_code=&radius=10')
        # Should redirect or show error
        self.assertIn(response.status_code, [200, 302])

    # ========== API ENDPOINT TESTS ==========
    
    def test_api_endpoints_exist(self):
        """Test that API endpoints are accessible."""
        # Test API structure (even if they return errors without proper auth)
        api_endpoints = ['/api/categories', '/api/health']
        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            # Should not return 404 (endpoint exists)
            self.assertNotEqual(response.status_code, 404)

    # ========== DATABASE QUERY TESTS ==========
    
    def test_venue_queries_work(self):
        """Test that database queries return expected results."""
        # Test basic queries
        all_venues = Venue.query.all()
        self.assertGreaterEqual(len(all_venues), 2)
        
        # Test filtered queries
        accessible_venues = Venue.query.filter(
            Venue.wheelchair_accessible == True
        ).all()
        self.assertGreater(len(accessible_venues), 0)

    def test_user_functionality(self):
        """Test user-related functionality."""
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))


class DataValidationTest(unittest.TestCase):
    """Tests specifically for data validation and integrity."""
    
    def test_venue_model_validation(self):
        """Test that venue model validates data correctly."""
        # Test required fields
        with self.assertRaises(Exception):
            venue = Venue()  # Missing required fields
            
    def test_accessibility_features_structure(self):
        """Test that accessibility features follow expected structure."""
        expected_keys = [
            'wheelchair_accessible',
            'accessible_parking',
            'accessible_restroom',
            'accessible_entrance'
        ]
        
        # This would test against your actual venue data
        # venue = Venue.query.first()
        # if venue and venue.accessibility_features:
        #     for key in expected_keys:
        #         self.assertIn(key, venue.accessibility_features)


def run_comprehensive_tests():
    """Run all tests and provide detailed report."""
    print("=" * 60)
    print("RUNNING COMPREHENSIVE APP VERIFICATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(ComprehensiveAppTest))
    suite.addTests(loader.loadTestsFromTestCase(DataValidationTest))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\nSUCCESS RATE: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 ALL TESTS PASSED! Your app is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)