#!/usr/bin/env python3
"""
Data Source Validation - Ensures all displayed data comes from real sources, not static/fake data.
Validates that venue data, accessibility scores, and user data are authentic.
"""

import sys
import json
import re
from datetime import datetime, timedelta
from app import create_app
from models import db
from models.venue import Venue, VenueCategory
from models.user import User
from models.review import UserReview, UserFavorite
from utils.accessibility import AccessibilityFilter
from utils.google_places import GooglePlacesAPI, VenueSearchService


class DataSourceValidator:
    """Validates that all data displayed in the app comes from legitimate sources."""
    
    def __init__(self):
        self.app = create_app()
        self.errors = []
        self.warnings = []
        self.validated_items = []
        
    def log_error(self, check, message):
        """Log a validation error."""
        self.errors.append(f"❌ {check}: {message}")
        print(f"❌ {check}: {message}")
        
    def log_warning(self, check, message):
        """Log a validation warning."""
        self.warnings.append(f"⚠️  {check}: {message}")
        print(f"⚠️  {check}: {message}")
        
    def log_success(self, check):
        """Log a successful validation."""
        self.validated_items.append(f"✅ {check}")
        print(f"✅ {check}")

    def validate_venue_data_authenticity(self):
        """Validate that venue data comes from real Google Places API or database."""
        print("\n🏢 VALIDATING VENUE DATA AUTHENTICITY")
        print("-" * 50)
        
        with self.app.app_context():
            venues = Venue.query.limit(10).all()  # Check first 10 venues
            
            if not venues:
                self.log_warning("Venue data", "No venues in database to validate")
                return
            
            for venue in venues:
                # Check for suspicious patterns that indicate fake data
                suspicious_patterns = [
                    ("Test", "Contains 'Test' in name"),
                    ("Example", "Contains 'Example' in name"),
                    ("Sample", "Contains 'Sample' in name"),
                    ("Lorem", "Contains Lorem ipsum text"),
                    ("123 Main St", "Generic test address"),
                    ("555-", "Fake phone number pattern")
                ]
                
                venue_suspicious = False
                for pattern, reason in suspicious_patterns:
                    if pattern.lower() in (venue.name or "").lower():
                        self.log_error(f"Venue {venue.id} name", f"Suspicious test data: {reason}")
                        venue_suspicious = True
                    if pattern.lower() in (venue.address or "").lower():
                        self.log_error(f"Venue {venue.id} address", f"Suspicious test data: {reason}")
                        venue_suspicious = True
                    if venue.phone and pattern in venue.phone:
                        self.log_error(f"Venue {venue.id} phone", f"Suspicious test data: {reason}")
                        venue_suspicious = True
                
                # Validate coordinate ranges (realistic lat/lng)
                if venue.latitude and venue.longitude:
                    if not (-90 <= venue.latitude <= 90):
                        self.log_error(f"Venue {venue.id} coordinates", f"Invalid latitude: {venue.latitude}")
                        venue_suspicious = True
                    if not (-180 <= venue.longitude <= 180):
                        self.log_error(f"Venue {venue.id} coordinates", f"Invalid longitude: {venue.longitude}")
                        venue_suspicious = True
                    
                    # Check for obviously fake coordinates (0,0 or repeated values)
                    if venue.latitude == 0 and venue.longitude == 0:
                        self.log_warning(f"Venue {venue.id} coordinates", "Suspicious (0,0) coordinates")
                    
                    # Check if multiple venues have identical coordinates (suspicious)
                    similar_coords = Venue.query.filter(
                        Venue.latitude == venue.latitude,
                        Venue.longitude == venue.longitude,
                        Venue.id != venue.id
                    ).count()
                    if similar_coords > 2:
                        self.log_warning(f"Venue {venue.id} coordinates", f"{similar_coords} venues share same coordinates")
                
                # Validate Google Places integration
                if hasattr(venue, 'google_place_id') and venue.google_place_id:
                    if not venue.google_place_id.startswith('ChIJ'):  # Google Place IDs start with ChIJ
                        self.log_error(f"Venue {venue.id} Google Place ID", "Invalid Google Place ID format")
                        venue_suspicious = True
                
                # Check for realistic accessibility features
                if venue.accessibility_features:
                    if not isinstance(venue.accessibility_features, dict):
                        self.log_error(f"Venue {venue.id} accessibility", "Accessibility features not in dict format")
                        venue_suspicious = True
                    else:
                        # Validate accessibility feature keys
                        expected_keys = [
                            'wheelchair_accessible', 'accessible_parking', 
                            'accessible_restroom', 'accessible_entrance'
                        ]
                        for key in venue.accessibility_features.keys():
                            if key not in expected_keys and not key.startswith('accessible_'):
                                self.log_warning(f"Venue {venue.id} accessibility", f"Unexpected feature key: {key}")
                
                if not venue_suspicious:
                    self.log_success(f"Venue {venue.id} ({venue.name[:30]}...)")

    def validate_accessibility_scores(self):
        """Validate that accessibility scores are calculated from real data, not hardcoded."""
        print("\n♿ VALIDATING ACCESSIBILITY SCORE CALCULATIONS")
        print("-" * 50)
        
        with self.app.app_context():
            venues = Venue.query.limit(5).all()
            
            for venue in venues:
                if not venue.accessibility_features:
                    self.log_warning(f"Venue {venue.id} score", "No accessibility features to score")
                    continue
                
                # Calculate score using the actual algorithm
                calculated_score = AccessibilityFilter.calculate_accessibility_score(venue)
                
                # Validate score is in expected range
                if not 0 <= calculated_score <= 100:
                    self.log_error(f"Venue {venue.id} score", f"Score outside valid range: {calculated_score}")
                    continue
                
                # Verify score correlates with features
                features = venue.accessibility_features
                wheelchair_accessible = features.get('wheelchair_accessible', False)
                
                # If venue claims to be wheelchair accessible, score should be reasonable
                if wheelchair_accessible and calculated_score < 30:
                    self.log_warning(f"Venue {venue.id} score", 
                                   f"Low score ({calculated_score}) despite wheelchair accessibility")
                
                # If no accessibility features, score should be low
                accessible_features = sum(1 for v in features.values() if v is True)
                if accessible_features == 0 and calculated_score > 20:
                    self.log_warning(f"Venue {venue.id} score", 
                                   f"High score ({calculated_score}) with no accessible features")
                
                self.log_success(f"Venue {venue.id} accessibility score: {calculated_score}%")

    def validate_user_data_authenticity(self):
        """Validate that user data is realistic and not obviously fake."""
        print("\n👤 VALIDATING USER DATA AUTHENTICITY")
        print("-" * 50)
        
        with self.app.app_context():
            users = User.query.limit(10).all()
            
            if not users:
                self.log_warning("User data", "No users in database to validate")
                return
            
            for user in users:
                # Check for test/fake user patterns
                suspicious_patterns = [
                    'test', 'fake', 'example', 'sample', 'demo', 'admin'
                ]
                
                user_suspicious = False
                for pattern in suspicious_patterns:
                    if pattern in user.username.lower():
                        self.log_error(f"User {user.id}", f"Suspicious username: {user.username}")
                        user_suspicious = True
                    if pattern in user.email.lower():
                        self.log_error(f"User {user.id}", f"Suspicious email: {user.email}")
                        user_suspicious = True
                
                # Validate email format
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, user.email):
                    self.log_error(f"User {user.id}", f"Invalid email format: {user.email}")
                    user_suspicious = True
                
                # Check for realistic zip codes
                if user.home_zip_code:
                    if not user.home_zip_code.isdigit() or len(user.home_zip_code) != 5:
                        self.log_warning(f"User {user.id}", f"Unusual zip code: {user.home_zip_code}")
                
                if not user_suspicious:
                    self.log_success(f"User {user.id} ({user.username})")

    def validate_review_data_authenticity(self):
        """Validate that reviews are realistic and not obviously generated."""
        print("\n⭐ VALIDATING REVIEW DATA AUTHENTICITY")
        print("-" * 50)
        
        with self.app.app_context():
            reviews = UserReview.query.limit(10).all()
            
            if not reviews:
                self.log_warning("Review data", "No reviews in database to validate")
                return
            
            for review in reviews:
                # Check for fake review patterns
                suspicious_phrases = [
                    'lorem ipsum', 'test review', 'this is a test', 
                    'sample comment', 'fake review', 'example review'
                ]
                
                review_suspicious = False
                if review.comment:
                    for phrase in suspicious_phrases:
                        if phrase.lower() in review.comment.lower():
                            self.log_error(f"Review {review.id}", f"Suspicious comment: contains '{phrase}'")
                            review_suspicious = True
                
                # Validate rating range
                if not 1 <= review.rating <= 5:
                    self.log_error(f"Review {review.id}", f"Invalid rating: {review.rating}")
                    review_suspicious = True
                
                # Check for realistic timestamp
                if review.created_at > datetime.utcnow():
                    self.log_error(f"Review {review.id}", "Future timestamp")
                    review_suspicious = True
                
                # Check if review is too old (might indicate bulk import of fake data)
                if review.created_at < datetime.utcnow() - timedelta(days=3650):  # 10 years
                    self.log_warning(f"Review {review.id}", "Very old review (>10 years)")
                
                if not review_suspicious:
                    self.log_success(f"Review {review.id} (Rating: {review.rating})")

    def validate_search_results_authenticity(self):
        """Validate that search results come from real API calls, not static data."""
        print("\n🔍 VALIDATING SEARCH RESULT AUTHENTICITY")
        print("-" * 50)
        
        with self.app.app_context():
            # Test if Google Places API is actually being called
            try:
                google_api = GooglePlacesAPI(self.app.config.get('GOOGLE_PLACES_API_KEY'))
                venue_service = VenueSearchService(google_api)
                
                # Try a search and validate response structure
                test_venues = venue_service.search_nearby_venues(
                    latitude=40.7128, longitude=-74.0060, radius=1000, category=None
                )
                
                if test_venues:
                    # Check if results have Google Places characteristics
                    sample_venue = test_venues[0]
                    
                    # Real Google Places results should have place_id
                    if not hasattr(sample_venue, 'google_place_id') or not sample_venue.google_place_id:
                        self.log_warning("Search results", "Results missing Google Place IDs")
                    
                    # Real results should have realistic coordinates
                    if sample_venue.latitude == 0 and sample_venue.longitude == 0:
                        self.log_error("Search results", "Results have invalid (0,0) coordinates")
                    
                    self.log_success(f"Search returned {len(test_venues)} venues with valid structure")
                else:
                    self.log_warning("Search results", "Search returned no results (API might be disabled)")
                    
            except Exception as e:
                self.log_error("Search functionality", f"Search failed: {e}")

    def validate_database_integrity(self):
        """Check for data consistency and referential integrity."""
        print("\n🗄️  VALIDATING DATABASE INTEGRITY")
        print("-" * 50)
        
        with self.app.app_context():
            # Check for orphaned records
            venues_without_categories = Venue.query.filter_by(category_id=None).count()
            if venues_without_categories > 0:
                self.log_warning("Database integrity", f"{venues_without_categories} venues without categories")
            
            # Check for reviews without valid venues
            invalid_venue_reviews = db.session.query(UserReview).filter(
                ~UserReview.venue_id.in_(db.session.query(Venue.id))
            ).count()
            if invalid_venue_reviews > 0:
                self.log_error("Database integrity", f"{invalid_venue_reviews} reviews for non-existent venues")
            
            # Check for reviews without valid users
            invalid_user_reviews = db.session.query(UserReview).filter(
                ~UserReview.user_id.in_(db.session.query(User.id))
            ).count()
            if invalid_user_reviews > 0:
                self.log_error("Database integrity", f"{invalid_user_reviews} reviews from non-existent users")
            
            # Check for duplicate venues (same name + address)
            duplicate_venues = db.session.query(Venue.name, Venue.address, db.func.count(Venue.id)).group_by(
                Venue.name, Venue.address
            ).having(db.func.count(Venue.id) > 1).all()
            
            if duplicate_venues:
                self.log_warning("Database integrity", f"{len(duplicate_venues)} sets of duplicate venues found")
            
            self.log_success("Database integrity checks completed")

    def validate_api_responses(self):
        """Test actual API endpoints to ensure they return real data."""
        print("\n🌐 VALIDATING API RESPONSE AUTHENTICITY")
        print("-" * 50)
        
        with self.app.app_context():
            client = self.app.test_client()
            
            # Test venue detail API
            venue = Venue.query.first()
            if venue:
                response = client.get(f'/venue/{venue.id}')
                if response.status_code == 200:
                    # Check if response contains actual venue data
                    if venue.name.encode() in response.data:
                        self.log_success(f"Venue detail API returns real data for venue {venue.id}")
                    else:
                        self.log_error("Venue detail API", "Response doesn't contain expected venue data")
                else:
                    self.log_error("Venue detail API", f"Failed with status {response.status_code}")
            
            # Test search API
            response = client.get('/search?zip_code=10001&radius=10')
            if response.status_code == 200:
                if b'Search Results' in response.data:
                    self.log_success("Search API returns structured results")
                else:
                    self.log_warning("Search API", "Unexpected response format")

    def run_all_validations(self):
        """Run all data source validations."""
        print("🔍 DATA SOURCE VALIDATION STARTING")
        print("=" * 60)
        
        self.validate_venue_data_authenticity()
        self.validate_accessibility_scores()
        self.validate_user_data_authenticity()
        self.validate_review_data_authenticity()
        self.validate_search_results_authenticity()
        self.validate_database_integrity()
        self.validate_api_responses()
        
        self.print_summary()

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("DATA SOURCE VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"✅ Validations Passed: {len(self.validated_items)}")
        print(f"❌ Errors Found: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ CRITICAL DATA ISSUES:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n⚠️  DATA QUALITY WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 ALL DATA SOURCES VALIDATED! Your data is authentic and properly sourced.")
        elif not self.errors:
            print("\n✅ No critical data issues. Review warnings for data quality improvements.")
        else:
            print("\n🛠️  Critical data issues found. Fix these before deployment!")
        
        print(f"\n📊 DATA AUTHENTICITY SCORE: {self.calculate_authenticity_score():.1f}%")
        
        return len(self.errors) == 0

    def calculate_authenticity_score(self):
        """Calculate overall data authenticity score."""
        total_items = len(self.validated_items) + len(self.errors) + len(self.warnings)
        if total_items == 0:
            return 0
        
        score = (len(self.validated_items) / total_items) * 100
        # Reduce score for errors more than warnings
        score -= (len(self.errors) * 10)  # -10% per error
        score -= (len(self.warnings) * 2)  # -2% per warning
        
        return max(0, min(100, score))


def main():
    """Run data source validation."""
    validator = DataSourceValidator()
    success = validator.run_all_validations()
    
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS:")
    print("="*60)
    print("1. Run this validation after every data import")
    print("2. Monitor for patterns indicating fake/test data")
    print("3. Verify Google Places API integration regularly")
    print("4. Check database integrity weekly")
    print("5. Validate user-generated content for authenticity")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())