import sqlite3
import os

# Connect to database
db_path = 'db/db.sqlite3'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Bookkeeping tables ===")
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "bookkeeping%"')
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

print("\n=== Django migrations table ===")
cursor.execute('SELECT app, name FROM django_migrations WHERE app="bookkeeping" ORDER BY name')
migrations = cursor.fetchall()
for migration in migrations:
    print(f"- {migration[0]}.{migration[1]}")

print("\n=== Asset table structure ===")
try:
    cursor.execute('PRAGMA table_info(bookkeeping_asset)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
        
    print("\n=== Asset table data ===")
    cursor.execute('SELECT * FROM bookkeeping_asset')
    assets = cursor.fetchall()
    for asset in assets:
        print(f"- {asset}")
except sqlite3.OperationalError as e:
    print(f"Asset table error: {e}")

print("\n=== Transaction table structure ===")
try:
    cursor.execute('PRAGMA table_info(bookkeeping_transaction)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except sqlite3.OperationalError as e:
    print(f"Transaction table error: {e}")

print("\n=== Check for foreign key issues ===")
try:
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%associate%" OR name LIKE "%report%"')
    related_tables = cursor.fetchall()
    for table in related_tables:
        print(f"- {table[0]}")
        try:
            cursor.execute(f'PRAGMA table_info({table[0]})')
            columns = cursor.fetchall()
            for col in columns:
                if 'asset' in col[1].lower():
                    print(f"  - {col[1]} ({col[2]})")
        except:
            pass
except Exception as e:
    print(f"Error checking related tables: {e}")

conn.close()
