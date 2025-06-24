#!/usr/bin/env python3
"""
Reset Database Fresh - Clean out fake events and venues for fresh start
"""
import sys
import os
import sqlite3
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def reset_database_fresh():
    """Clean out fake/generated data and reset to fresh state"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'accessible_outings.db')
    
    print(f"🧹 Resetting database to fresh state: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current counts before cleanup
        cursor.execute("SELECT COUNT(*) FROM events")
        events_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM venues")
        venues_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_before = cursor.fetchone()[0]
        
        print(f"\n📊 Current Database State:")
        print(f"  Events: {events_before}")
        print(f"  Venues: {venues_before}")
        print(f"  Users: {users_before}")
        
        print(f"\n🗑️  Cleaning up data...")
        
        # 1. Delete all auto-generated/fake events
        cursor.execute("DELETE FROM event_favorites WHERE event_id IN (SELECT id FROM events WHERE source IN ('auto_generated', 'generated', 'sample'))")
        favorites_deleted = cursor.rowcount
        
        cursor.execute("DELETE FROM event_reviews WHERE event_id IN (SELECT id FROM events WHERE source IN ('auto_generated', 'generated', 'sample'))")
        reviews_deleted = cursor.rowcount
        
        cursor.execute("DELETE FROM events WHERE source IN ('auto_generated', 'generated', 'sample')")
        events_deleted = cursor.rowcount
        
        print(f"  ✅ Deleted {events_deleted} fake events")
        print(f"  ✅ Deleted {favorites_deleted} event favorites")
        print(f"  ✅ Deleted {reviews_deleted} event reviews")
        
        # 2. Delete venues that have no Google Place ID (fake venues)
        cursor.execute("""
            DELETE FROM user_favorites 
            WHERE venue_id IN (
                SELECT id FROM venues 
                WHERE google_place_id IS NULL 
                OR google_place_id = ''
            )
        """)
        user_favorites_deleted = cursor.rowcount
        
        cursor.execute("""
            DELETE FROM user_reviews 
            WHERE venue_id IN (
                SELECT id FROM venues 
                WHERE google_place_id IS NULL 
                OR google_place_id = ''
            )
        """)
        user_reviews_deleted = cursor.rowcount
        
        cursor.execute("""
            DELETE FROM venues 
            WHERE google_place_id IS NULL 
            OR google_place_id = ''
        """)
        venues_deleted = cursor.rowcount
        
        print(f"  ✅ Deleted {venues_deleted} fake/invalid venues")
        print(f"  ✅ Deleted {user_favorites_deleted} venue favorites")
        print(f"  ✅ Deleted {user_reviews_deleted} venue reviews")
        
        # 3. Clean up search history for non-productive searches
        cursor.execute("DELETE FROM search_history WHERE results_count = 0")
        searches_deleted = cursor.rowcount
        print(f"  ✅ Deleted {searches_deleted} empty search records")
        
        # 4. Reset API cache to force fresh data
        try:
            cursor.execute("DELETE FROM api_cache WHERE created_at < datetime('now', '-1 day')")
            cache_deleted = cursor.rowcount
            print(f"  ✅ Deleted {cache_deleted} old API cache entries")
        except:
            print("  ℹ️  No API cache table found (skipping)")
        
        # 5. Keep essential data: users, categories, and real venues with Google Place IDs
        
        conn.commit()
        
        # Get final counts
        cursor.execute("SELECT COUNT(*) FROM events")
        events_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM venues")
        venues_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM venue_categories")
        categories_count = cursor.fetchone()[0]
        
        print(f"\n📈 Final Database State:")
        print(f"  Events: {events_after} (removed {events_before - events_after})")
        print(f"  Venues: {venues_after} (removed {venues_before - venues_after})")
        print(f"  Users: {users_after} (preserved)")
        print(f"  Categories: {categories_count} (preserved)")
        
        # Show what remains
        cursor.execute("SELECT COUNT(*) FROM venues WHERE google_place_id IS NOT NULL AND google_place_id != ''")
        real_venues = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE source_api IS NOT NULL")
        api_events = cursor.fetchone()[0]
        
        print(f"\n🎯 Clean Database Summary:")
        print(f"  Real venues (with Google Place ID): {real_venues}")
        print(f"  API-sourced events: {api_events}")
        print(f"  Categories available: {categories_count}")
        
        # Reset auto-increment counters to clean up gaps
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('events', 'venues')")
            print(f"  ✅ Reset ID sequences for clean numbering")
        except:
            pass
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def show_remaining_data():
    """Show what data remains after cleanup"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'accessible_outings.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n🔍 Remaining Data Details:")
        
        # Show remaining venues by category
        cursor.execute("""
            SELECT vc.name, COUNT(v.id) as venue_count
            FROM venue_categories vc
            LEFT JOIN venues v ON vc.id = v.category_id
            GROUP BY vc.id, vc.name
            ORDER BY venue_count DESC, vc.name
        """)
        
        categories = cursor.fetchall()
        print(f"\n  📍 Venues by Category:")
        for cat_name, count in categories:
            print(f"    {cat_name}: {count} venues")
        
        # Show remaining events by source
        cursor.execute("""
            SELECT COALESCE(source_api, source, 'unknown') as source_type, COUNT(*) as count
            FROM events
            GROUP BY source_type
            ORDER BY count DESC
        """)
        
        event_sources = cursor.fetchall()
        if event_sources:
            print(f"\n  📅 Events by Source:")
            for source, count in event_sources:
                print(f"    {source}: {count} events")
        else:
            print(f"\n  📅 No events remaining (clean slate for Eventbrite)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing remaining data: {e}")

def main():
    """Main function"""
    print("🧹 Database Fresh Reset Tool")
    print("=" * 50)
    print("This will remove all fake/generated events and venues,")
    print("keeping only real venues with Google Place IDs and user accounts.")
    print()
    
    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Reset cancelled.")
        return 1
    
    success = reset_database_fresh()
    
    if success:
        show_remaining_data()
        print("\n✅ Database reset completed successfully!")
        print("\n🎯 Next Steps:")
        print("1. Restart your Flask application")
        print("2. Test search with ZIP 02114 - should pull fresh Eventbrite events")
        print("3. New venues will be created automatically from Eventbrite events")
        print("4. All events will now be real from Eventbrite API")
        
    else:
        print("\n❌ Database reset failed!")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())