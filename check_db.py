import sqlite3
import os

path = os.path.join(os.getcwd(), 'db.sqlite3')
print('DB path:', path)
conn = sqlite3.connect(path)
cur = conn.cursor()
print('Tables:')
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print('  ', row[0])
print('coffee_specialist exists:', cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coffee_specialist'").fetchone())
print('coffee_especialista exists:', cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coffee_especialista'").fetchone())
print('coffee_specialist columns:', list(cur.execute('PRAGMA table_info(coffee_specialist)')))
print('coffee_especialista columns:', list(cur.execute('PRAGMA table_info(coffee_especialista)')))
print('Specialist count if table exists:')
try:
    print(cur.execute('SELECT count(*) FROM coffee_specialist').fetchone())
except Exception as e:
    print('  ERROR:', e)
conn.close()
