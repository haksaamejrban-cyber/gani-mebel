import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT nodes, connections FROM workflow_entity WHERE id='KNTaJvjMpXXpIHmf'")
row = cur.fetchone()
if row:
    nodes = json.loads(row[0])
    connections = json.loads(row[1])

    print('=== ALL NODES ===')
    for node in nodes:
        print(f"  {node['name']} ({node['type']})")

    print('\n=== Global Config ===')
    for node in nodes:
        if 'global config' in node['name'].lower() or 'config' in node['name'].lower():
            print(json.dumps(node, ensure_ascii=False, indent=2))

    print('\n=== Start Typing connections (what comes before) ===')
    # Find what connects TO Start Typing
    for src, targets in connections.items():
        for port, dests in targets.items():
            for dest_list in dests:
                for dest in dest_list:
                    if 'typing' in dest.get('node', '').lower():
                        print(f"  {src} -> {dest['node']} (port {dest.get('index',0)})")

conn.close()
