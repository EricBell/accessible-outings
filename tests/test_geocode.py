import unittest
from app import app, db
# from models.venue import VenueCategory
# from models.user import User
from unittest.mock import patch
import os
import utils.geocoding as geocoding

class GeocodeTestCase(unittest.TestCase):
    def setUp(self):
        print('setup')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()



    @patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "testkey"})
    def test_standalone_positive(self):
        print('pos')
        """Positive test: main() should print the correct API key and instantiate GeocodingService."""
        with patch("builtins.print") as mock_print:
            geocoding.main()
            # Check that the API key was printed
            mock_print.assert_any_call("google api key ", "testkey")
            # Check that the GeocodingService object was printed
            self.assertTrue(any("geo svc" in str(call) for call in mock_print.call_args_list))

    @patch.dict(os.environ, {}, clear=True)
    @patch('dotenv.load_dotenv')
    def test_standalone_negative(self, mock_load_dotenv):
        print('neg')
        """Negative test: main() should print None for missing API key and still instantiate GeocodingService."""
        with patch("builtins.print") as mock_print:
            geocoding.main()

            
            # Should print None for the API key
            mock_print.assert_any_call("google api key ", None)
            # Should still print the GeocodingService object
            self.assertTrue(any("geo svc" in str(call) for call in mock_print.call_args_list))


if __name__ == "__main__":
    unittest.main()

 
