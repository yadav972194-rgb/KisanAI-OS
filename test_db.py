import sqlite3
conn = sqlite3.connect('kisanai.db')
cursor = conn.cursor()

# List tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:')
for t in tables:
    print('  ' + t[0])

# Count rows in key tables
for table in ['users', 'farmers', 'crops', 'soils', 'diseases', 'user_sessions', 'otp_codes', 'farms', 'my_farm_crops']:
    try:
        cursor.execute('SELECT COUNT(*) FROM ' + table)
        count = cursor.fetchone()[0]
        print('  ' + table + ': ' + str(count) + ' rows')
    except Exception as e:
        print('  ' + table + ': ERROR - ' + str(e))

conn.close()