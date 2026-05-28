import sqlite3
import os

path = os.path.join(os.getcwd(), 'db.sqlite3')
conn = sqlite3.connect(path)
cur = conn.cursor()
print('before cols:', list(cur.execute("PRAGMA table_info(coffee_servicio_specialists)")))
cur.execute('ALTER TABLE coffee_servicio_specialists RENAME COLUMN especialista_id TO specialist_id')
conn.commit()
print('after cols:', list(cur.execute("PRAGMA table_info(coffee_servicio_specialists)")))
print('foreign keys:', list(cur.execute("PRAGMA foreign_key_list(coffee_servicio_specialists)")))
conn.close()
