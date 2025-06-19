#!/usr/bin/env python3
"""
Script to update existing venues with proper category assignments.
This script will analyze venue names and Google Place types to assign appropriate categories.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.venue import Venue
from utils.google_places import GooglePlacesAPI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_venue_categories():
    """Update existing venues with category assignments."""
    app = create_app()
    
    with app.app_context():
        # Get all venues without categories
        venues_without_categories = Venue.query.filter(Venue.category_id.is_(None)).all()
        
        logger.info(f"Found {len(venues_without_categories)} venues without categories")
        
        if not venues_without_categories:
            logger.info("All venues already have categories assigned")
            return
        
        # Initialize Google Places API for category mapping
        google_api = GooglePlacesAPI(app.config.get('GOOGLE_PLACES_API_KEY', ''))
        
        updated_count = 0
        
        for venue in venues_without_categories:
            try:
                # Create mock place data from venue information
                place_data = {
                    'place_id': venue.google_place_id,
                    'name': venue.name,
                    'types': [],  # We don't have stored types, so rely on name-based categorization
                }
                
                # Try to get category based on venue name
                category_id = google_api.map_google_types_to_category(place_data)
                
                if category_id:
                    venue.category_id = category_id
                    updated_count += 1
                    logger.info(f"Assigned category {category_id} to venue: {venue.name}")
                else:
                    logger.warning(f"Could not categorize venue: {venue.name}")
            
            except Exception as e:
                logger.error(f"Error processing venue {venue.name}: {e}")
                continue
        
        # Commit changes
        if updated_count > 0:
            try:
                db.session.commit()
                logger.info(f"Successfully updated {updated_count} venues with categories")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error committing changes: {e}")
        else:
            logger.info("No venues were categorized")

def show_category_stats():
    """Show statistics about venue categories."""
    app = create_app()
    
    with app.app_context():
        from models.venue import VenueCategory
        
        categories = VenueCategory.query.all()
        total_venues = Venue.query.count()
        categorized_venues = Venue.query.filter(Venue.category_id.isnot(None)).count()
        uncategorized_venues = total_venues - categorized_venues
        
        print(f"\n=== Venue Category Statistics ===")
        print(f"Total venues: {total_venues}")
        print(f"Categorized venues: {categorized_venues}")
        print(f"Uncategorized venues: {uncategorized_venues}")
        print(f"\nBreakdown by category:")
        
        for category in categories:
            count = category.get_venues_count()
            accessible_count = category.get_accessible_venues_count()
            print(f"  {category.name}: {count} venues ({accessible_count} accessible)")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        show_category_stats()
    else:
        print("Updating venue categories...")
        update_venue_categories()
        print("\nShowing updated statistics...")
        show_category_stats()