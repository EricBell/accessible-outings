import unittest
from app import app, db
from models.venue import VenueCategory
from models.user import User

class GeocodeTestCase(unittest.TestCase):
    def setUp(self):
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

    def testStandalon(self):
        pass


if __name__ == "__main__":
    unittest.main()