#!/usr/bin/env python3
"""
Simple debug script to check venue data without Flask dependencies.
"""

import sqlite3
import os

def check_venues():
    """Check venue data directly from SQLite database."""
    db_path = '../instance/accessible_outings.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check total venues
    cursor.execute("SELECT COUNT(*) FROM venues")
    total_venues = cursor.fetchone()[0]
    print(f"Total venues: {total_venues}")
    
    # Check venues with categories
    cursor.execute("SELECT COUNT(*) FROM venues WHERE category_id IS NOT NULL")
    categorized_venues = cursor.fetchone()[0]
    print(f"Categorized venues: {categorized_venues}")
    
    # Show some venue names to understand the data
    cursor.execute("SELECT name, category_id FROM venues LIMIT 10")
    venues = cursor.fetchall()
    print(f"\nFirst 10 venues:")
    for name, category_id in venues:
        print(f"  {name} (category: {category_id})")
    
    # Check categories
    cursor.execute("SELECT id, name FROM venue_categories")
    categories = cursor.fetchall()
    print(f"\nAvailable categories:")
    for cat_id, cat_name in categories:
        cursor.execute("SELECT COUNT(*) FROM venues WHERE category_id = ?", (cat_id,))
        count = cursor.fetchone()[0]
        print(f"  {cat_id}: {cat_name} ({count} venues)")
    
    conn.close()

if __name__ == '__main__':
    check_venues()