#!/usr/bin/env python3
"""
Direct SQLite script to fix venue categories without Flask dependencies.
"""

import sqlite3
import os

def map_venue_to_category(venue_name):
    """Map venue name to category ID."""
    name_lower = venue_name.lower()
    
    # Theaters (id: 9)
    if any(keyword in name_lower for keyword in ['amc', 'cinema', 'theater', 'theatre', 'movie', 'cineplex', 'regal']):
        return 9
    
    # Shopping Centers (id: 5)  
    elif any(keyword in name_lower for keyword in ['target', 'walmart', 'mall', 'shopping', 'department store', 'costco', 'home depot', 'lowes', 'best buy', 'barnes & noble', 'burlington', 'jcpenney', 'charlotte russe']):
        return 5
    
    # Museums (id: 3)
    elif any(keyword in name_lower for keyword in ['museum', 'gallery', 'art center', 'history', 'science center']):
        return 3
    
    # Libraries (id: 8)
    elif any(keyword in name_lower for keyword in ['library', 'public library']):
        return 8
    
    # Aquariums (id: 4)
    elif any(keyword in name_lower for keyword in ['aquarium', 'sea life', 'marine', 'zoo']):
        return 4
    
    # Botanical Gardens (id: 1)
    elif any(keyword in name_lower for keyword in ['botanical', 'garden', 'arboretum', 'conservatory', 'greenhouse']):
        return 1
    
    # Bird Watching (id: 2)
    elif any(keyword in name_lower for keyword in ['bird', 'aviary', 'nature center', 'wildlife', 'audubon']):
        return 2
    
    # Antique Shops (id: 6)
    elif any(keyword in name_lower for keyword in ['antique', 'vintage', 'collectible', 'consignment', 'thrift']):
        return 6
    
    # Art Galleries (id: 7)
    elif any(keyword in name_lower for keyword in ['art gallery', 'gallery', 'art studio', 'arts center']):
        return 7
    
    # Craft Stores (id: 10)
    elif any(keyword in name_lower for keyword in ['craft', 'hobby', 'michaels', 'joann', 'art supply', 'fabric']):
        return 10
    
    # Garden Centers (id: 11)
    elif any(keyword in name_lower for keyword in ['nursery', 'garden center', 'plant', 'florist', 'greenhouse']):
        return 11
    
    # Conservatories (id: 12) - harder to detect
    elif any(keyword in name_lower for keyword in ['conservatory', 'glass house', 'tropical house', 'palm house']):
        return 12
    
    return None

def update_venue_categories():
    """Update venue categories directly in SQLite."""
    db_path = '../instance/accessible_outings.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all venues without categories
    cursor.execute("SELECT id, name FROM venues WHERE category_id IS NULL")
    venues = cursor.fetchall()
    
    print(f"Found {len(venues)} venues without categories")
    
    updated_count = 0
    for venue_id, venue_name in venues:
        category_id = map_venue_to_category(venue_name)
        
        if category_id:
            cursor.execute("UPDATE venues SET category_id = ? WHERE id = ?", (category_id, venue_id))
            updated_count += 1
            print(f"Updated {venue_name} -> Category {category_id}")
        else:
            print(f"No category found for: {venue_name}")
    
    conn.commit()
    print(f"\nUpdated {updated_count} venues")
    
    # Show results
    print("\nCategory breakdown:")
    cursor.execute("""
        SELECT vc.name, COUNT(v.id) as venue_count
        FROM venue_categories vc
        LEFT JOIN venues v ON vc.id = v.category_id
        GROUP BY vc.id, vc.name
        ORDER BY venue_count DESC
    """)
    
    for category_name, count in cursor.fetchall():
        print(f"  {category_name}: {count} venues")
    
    conn.close()

if __name__ == '__main__':
    update_venue_categories()