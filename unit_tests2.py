import unittest
from app import app, db
from models.venue import Venue


class VenueDetailTemplateTest(unittest.TestCase):
    """Single focused test for venue detail template functionality."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['GOOGLE_PLACES_API_KEY'] = 'test-api-key'
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        self._create_test_venue()

    def tearDown(self):
        """Clean up after test."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_test_venue(self):
        """Create a single test venue."""
        venue = Venue(
            name='Test Restaurant',
            address='123 Main St',
            city='Portsmouth',
            state='NH',
            zip_code='03801',
            latitude=43.0718,
            longitude=-70.7626,
            phone='(603) 555-0123',
            category_id=1,
            wheelchair_accessible=True
        )
        db.session.add(venue)
        db.session.commit()

    def test_venue_detail_page_renders_successfully(self):
        """Test that venue detail page renders without template error."""
        # This test will FAIL until venue_detail.html template is created
        # Once the template exists, this test should PASS
        response = self.client.get('/venue/1')
        
        # Should return 200 OK (not 500 Internal Server Error from missing template)
        self.assertEqual(response.status_code, 200)
        
        # Should contain venue name in the response
        self.assertIn(b'Test Restaurant', response.data)
        
        # Should contain basic venue information
        self.assertIn(b'123 Main St', response.data)
        self.assertIn(b'Portsmouth', response.data)


if __name__ == '__main__':
    unittest.main(verbosity=2)