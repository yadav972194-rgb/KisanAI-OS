import sqlite3
conn = sqlite3.connect('kisanai.db')
cursor = conn.cursor()

# List all tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = cursor.fetchall()
print('All Tables:')
for t in tables:
    print('  ' + t[0])

# Check my-farm related tables
print()
print('Checking my-farm related tables:')
for table in ['farms', 'my_farm_crops', 'farm_crops', 'user_farms']:
    try:
        cursor.execute('SELECT COUNT(*) FROM ' + table)
        count = cursor.fetchone()[0]
        print('  ' + table + ': ' + str(count) + ' rows')
    except Exception as e:
        print('  ' + table + ': MISSING - ' + str(e))

# Check schema of users table
cursor.execute('PRAGMA table_info(users)')
print()
print('users schema:')
for col in cursor.fetchall():
    print('  ' + str(col))

conn.close()