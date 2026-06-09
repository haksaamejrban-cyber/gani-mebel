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
run_data = outer[5]

def resolve(val, outer, depth=0):
    if depth > 20: return val
    if isinstance(val, str) and val.isdigit() and int(val) < len(outer):
        return resolve(outer[int(val)], outer, depth+1)
    if isinstance(val, dict):
        return {k: resolve(v, outer, depth+1) for k, v in val.items()}
    if isinstance(val, list):
        return [resolve(item, outer, depth+1) for item in val]
    return val

for node in ['Global Config', 'Start Typing', 'Stop Typing']:
    print(f'\n=== {node} ===')
    val = run_data.get(node)
    if val is None:
        print('  NOT FOUND'); continue

    resolved = resolve(val, outer)
    if isinstance(resolved, list) and resolved:
        run = resolved[0]
        err = run.get('error') if isinstance(run, dict) else None
        if err:
            print(f'  ERROR: {str(err)[:300]}')
        else:
            try:
                main_out = run.get('data', {}).get('main', [[]])
                items = main_out[0] if main_out else []
                for item in items[:2]:
                    j = item.get('json', {}) if isinstance(item, dict) else item
                    print(f'  OUTPUT: {str(j)[:300]}')
            except Exception as e:
                print(f'  OK (output err: {e})')
    else:
        print(f'  type: {type(resolved)}')

conn.close()
