#!/usr/bin/env python3
"""
Fix missing city names for venues by mapping NH zip codes to cities.
"""

from app import app
from models import db, Venue

# NH zip code to city mapping
NH_ZIP_TO_CITY = {
    '03301': 'Concord',
    '03302': 'Concord',
    '03303': 'Concord', 
    '03304': 'Bow',
    '03305': 'Concord',
    '03079': 'Salem',
    '03811': 'Atkinson',
    '03819': 'Durham',
    '03873': 'Sandown'
}

# MA zip code to city mapping (for nearby venues)
MA_ZIP_TO_CITY = {
    '01913': 'Amesbury',
    '01832': 'Haverhill',
    '01844': 'Methuen',
    '01835': 'Bradford'
}

def fix_missing_cities():
    """Fix missing city names for venues."""
    with app.app_context():
        venues = Venue.query.filter(Venue.city.is_(None)).all()
        updated_count = 0
        
        for venue in venues:
            if venue.state == 'NH' and venue.zip_code in NH_ZIP_TO_CITY:
                venue.city = NH_ZIP_TO_CITY[venue.zip_code]
                print(f"Updated {venue.name}: {venue.city}, {venue.state} {venue.zip_code}")
                updated_count += 1
            elif venue.state == 'MA' and venue.zip_code in MA_ZIP_TO_CITY:
                venue.city = MA_ZIP_TO_CITY[venue.zip_code]
                print(f"Updated {venue.name}: {venue.city}, {venue.state} {venue.zip_code}")
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"Successfully updated {updated_count} venues with city names.")
        else:
            print("No venues needed city updates.")

if __name__ == '__main__':
    fix_missing_cities()