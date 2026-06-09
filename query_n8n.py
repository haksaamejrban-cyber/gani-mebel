import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute('SELECT id, name, active FROM workflow_entity')
print('=== WORKFLOWS ===')
for r in cur.fetchall():
    print(r)

print('\n=== API KEYS ===')
try:
    cur.execute('SELECT * FROM user_api_keys LIMIT 5')
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print('user_api_keys error:', e)

try:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('\n=== TABLES ===')
    for r in cur.fetchall():
        print(r[0])
except Exception as e:
    print(e)

conn.close()
