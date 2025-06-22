#!/usr/bin/env python3
"""
Fix venue address parsing for existing venues in the database.
This script corrects the city, state, and zip fields that were parsed incorrectly.
"""

from app import app
from models import db, Venue

def fix_address_parsing():
    """Fix address parsing for all venues in the database."""
    with app.app_context():
        venues = Venue.query.all()
        updated_count = 0
        
        for venue in venues:
            # Skip if venue doesn't have address data
            if not venue.address:
                continue
                
            # Reconstruct the full address from what we know
            # Current state: address="96 Pleasant St", city="NH 03301", state=None, zip_code=None
            # We need to parse this correctly
            
            city_field = venue.city  # This currently contains "NH 03301" or similar
            if city_field and ' ' in city_field:
                # Check if city field contains state and zip (like "NH 03301")
                parts = city_field.split(' ')
                if len(parts) == 2 and len(parts[0]) == 2 and parts[1].isdigit():
                    # This looks like "NH 03301"
                    new_state = parts[0]
                    new_zip = parts[1]
                    
                    # Try to determine the actual city from context
                    # For now, we'll leave city empty since we can't reliably determine it
                    # from the current data structure
                    venue.state = new_state
                    venue.zip_code = new_zip
                    venue.city = None  # We'll need to get city from future API calls
                    
                    print(f"Updated {venue.name}:")
                    print(f"  State: {new_state}")
                    print(f"  Zip: {new_zip}")
                    print(f"  City: {venue.city} (cleared - will be populated by future searches)")
                    print()
                    
                    updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"Successfully updated {updated_count} venues.")
        else:
            print("No venues needed updating.")

if __name__ == '__main__':
    fix_address_parsing()