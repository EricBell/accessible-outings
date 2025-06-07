import unittest
from app import app, db
from models.venue import VenueCategory
from models.user import User

class AppTestCase(unittest.TestCase):
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

    def test_home_route(self):
        """Test that the home route returns 200 OK."""
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)

    def test_categories_initialized(self):
        """Test that categories are initialized in the database."""
        from app import _initialize_database
        _initialize_database(app)
        categories = VenueCategory.query.all()
        self.assertGreaterEqual(len(categories), 1)
        names = [cat.name for cat in categories]
        self.assertIn("Museums", names)

    def test_add_new_category(self):
        """Test adding a new category to the database."""
        new_cat = VenueCategory(
            name="Test Category",
            description="A test category",
            icon_class="fas fa-star",
            search_keywords=["test", "category"]
        )
        db.session.add(new_cat)
        db.session.commit()
        found = VenueCategory.query.filter_by(name="Test Category").first()
        self.assertIsNotNone(found)
        self.assertEqual(found.icon_class, "fas fa-star")

    def test_create_user(self):
        """Test creating a new user."""
        user = User.create_user(
            username="unittestuser",
            email="unittest@example.com",
            password="testpass",
            first_name="Unit",
            last_name="Test",
            home_zip_code="12345"
        )
        db.session.add(user)
        db.session.commit()
        found = User.query.filter_by(username="unittestuser").first()
        self.assertIsNotNone(found)
        self.assertEqual(found.email, "unittest@example.com")

    # Negative tests

    def test_category_not_found(self):
        """Test that querying a non-existent category returns None."""
        found = VenueCategory.query.filter_by(name="NonExistentCategory").first()
        self.assertIsNone(found)

    def test_user_not_found(self):
        """Test that querying a non-existent user returns None."""
        found = User.query.filter_by(username="no_such_user").first()
        self.assertIsNone(found)

    def test_home_route_not_found(self):
        """Test that a non-existent route returns 404."""
        response = self.app.get("/thispagedoesnotexist")
        self.assertEqual(response.status_code, 404)

    def test_duplicate_category(self):
        """Test that adding duplicate category names is not allowed if unique constraint exists."""
        new_cat1 = VenueCategory(
            name="Duplicate Category",
            description="First instance",
            icon_class="fas fa-star",
            search_keywords=["dup"]
        )
        db.session.add(new_cat1)
        db.session.commit()
        new_cat2 = VenueCategory(
            name="Duplicate Category",
            description="Second instance",
            icon_class="fas fa-star",
            search_keywords=["dup"]
        )
        db.session.add(new_cat2)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.rollback()

if __name__ == "__main__":
    unittest.main()