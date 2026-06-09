import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT nodes FROM workflow_entity WHERE id='KNTaJvjMpXXpIHmf'")
row = cur.fetchone()
if row:
    nodes = json.loads(row[0])
    for node in nodes:
        name = node.get('name', '')
        ntype = node.get('type', '')
        params = node.get('parameters', {})
        if 'typing' in name.lower() or 'typing' in str(params).lower() or 'http' in ntype.lower():
            print(f'\n=== {name} ({ntype}) ===')
            print(json.dumps(params, ensure_ascii=False, indent=2))
conn.close()
