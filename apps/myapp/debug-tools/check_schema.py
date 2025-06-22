#!/usr/bin/env python3
"""
Check database schema and column names.
"""

import sqlite3

def check_schema():
    """Check the users table schema."""
    conn = sqlite3.connect('../instance/accessible_outings.db')
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print("=== USERS TABLE SCHEMA ===")
    for col in columns:
        cid, name, data_type, not_null, default_value, pk = col
        print(f"Column {cid}: '{name}' ({data_type}) - Not Null: {not_null}, Default: {default_value}, PK: {pk}")
    
    # Get sample data with column names
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin_row = cursor.fetchone()
    
    if admin_row:
        print(f"\n=== ADMIN USER RAW DATA ===")
        column_names = [description[0] for description in cursor.description]
        for i, (col_name, value) in enumerate(zip(column_names, admin_row)):
            if col_name == 'password_hash':
                print(f"{i}: {col_name} = {value[:50]}... (length: {len(str(value))})")
            else:
                print(f"{i}: {col_name} = {repr(value)}")
    
    conn.close()

if __name__ == '__main__':
    check_schema()