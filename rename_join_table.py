import sqlite3
import os

path = os.path.join(os.getcwd(), 'db.sqlite3')
conn = sqlite3.connect(path)
cur = conn.cursor()
print('before tables:', [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
cur.execute('ALTER TABLE coffee_servicio_especialistas RENAME TO coffee_servicio_specialists')
conn.commit()
print('renamed')
print('after tables:', [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
print('new join cols', list(cur.execute('PRAGMA table_info(coffee_servicio_specialists)')))
conn.close()
