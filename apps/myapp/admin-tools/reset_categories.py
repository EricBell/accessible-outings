#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('../instance/accessible_outings.db')
cursor = conn.cursor()
cursor.execute("UPDATE venues SET category_id = NULL")
conn.commit()
print(f"Reset {cursor.rowcount} venues")
conn.close()