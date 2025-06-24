#!/usr/bin/env python3
"""
Update Events Schema - Add new API integration fields to events table
"""
import sys
import os
import sqlite3
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def update_events_schema():
    """Add new API integration fields to events table"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'accessible_outings.db')
    
    print(f"Updating events schema in database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(events)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        print(f"Current events table has {len(columns)} columns")
        
        # Add new columns if they don't exist
        new_columns = [
            ('source_api', 'VARCHAR(50)'),
            ('external_event_id', 'VARCHAR(100)'),
            ('last_verified', 'DATETIME'),
            ('verification_status', 'VARCHAR(20) DEFAULT "unverified"'),
            ('api_data', 'JSON')
        ]
        
        added_columns = []
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE events ADD COLUMN {column_name} {column_type}')
                    added_columns.append(column_name)
                    print(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"❌ Failed to add column {column_name}: {e}")
        
        if not added_columns:
            print("✅ All API integration columns already exist")
        else:
            print(f"✅ Successfully added {len(added_columns)} new columns")
        
        # Add indexes for better performance
        indexes = [
            ('idx_events_source_api', 'source_api'),
            ('idx_events_external_id', 'external_event_id'),
            ('idx_events_verification_status', 'verification_status'),
            ('idx_events_last_verified', 'last_verified')
        ]
        
        for index_name, column in indexes:
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON events ({column})')
                print(f"✅ Created index: {index_name}")
            except sqlite3.Error as e:
                print(f"❌ Failed to create index {index_name}: {e}")
        
        # Update existing events to have verification_status
        cursor.execute("UPDATE events SET verification_status = 'unverified' WHERE verification_status IS NULL")
        
        conn.commit()
        
        # Verify schema update
        cursor.execute("PRAGMA table_info(events)")
        updated_columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        print(f"\n📊 Events table now has {len(updated_columns)} columns:")
        for col_name, col_type in sorted(updated_columns.items()):
            marker = "🆕" if col_name in [col[0] for col in new_columns] else "  "
            print(f"  {marker} {col_name}: {col_type}")
        
        # Show some stats
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE source_api IS NOT NULL")
        api_events = cursor.fetchone()[0]
        
        print(f"\n📈 Event Statistics:")
        print(f"  Total events: {total_events}")
        print(f"  API sourced events: {api_events}")
        print(f"  Legacy events: {total_events - api_events}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Events Schema Updater")
    print("=" * 50)
    
    success = update_events_schema()
    
    if success:
        print("\n✅ Schema update completed successfully!")
        print("\nThe events table is now ready for Eventbrite API integration.")
        print("\nNext steps:")
        print("1. Add your Eventbrite API key to .env file")
        print("2. Test the event search functionality")
        print("3. Verify events are being pulled from Eventbrite")
    else:
        print("\n❌ Schema update failed!")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())