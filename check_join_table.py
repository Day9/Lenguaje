import sqlite3
import os

path = os.path.join(os.getcwd(), 'db.sqlite3')
conn = sqlite3.connect(path)
cur = conn.cursor()
print('join table exists:', cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coffee_servicio_specialists'").fetchone())
print('old join table exists:', cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coffee_servicio_especialistas'").fetchone())
print('old join columns:', list(cur.execute('PRAGMA table_info(coffee_servicio_especialistas)')))
print('foreign keys:', list(cur.execute('PRAGMA foreign_key_list(coffee_servicio_especialistas)')))
conn.close()
