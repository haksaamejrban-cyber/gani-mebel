import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT data FROM execution_data WHERE executionId=1811")
row = cur.fetchone()
raw = row[0]
if isinstance(raw, bytes):
    raw = raw.decode('utf-8', errors='replace')

outer = json.loads(raw)
print(f'Outer type: {type(outer)}, len: {len(outer)}')

# Find runData somewhere in the structure
def find_rundata(obj, depth=0):
    if depth > 5: return
    if isinstance(obj, dict):
        if 'runData' in obj:
            rd = obj['runData']
            if isinstance(rd, dict):
                print(f'  Found runData (depth={depth}): keys={list(rd.keys())}')
                for k, v in rd.items():
                    if 'typing' in k.lower() or 'config' in k.lower() or 'start' in k.lower() or 'stop' in k.lower():
                        print(f'    -> {k}: {str(v)[:200]}')
            else:
                print(f'  runData is {type(rd)}: {str(rd)[:100]}')
        for v in obj.values():
            find_rundata(v, depth+1)
    elif isinstance(obj, list):
        for item in obj:
            find_rundata(item, depth+1)

find_rundata(outer)
conn.close()
