import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

def deref(val, arr):
    """Resolve numeric string references in n8n's compressed format"""
    if isinstance(val, str) and val.isdigit():
        return deref(arr[int(val)], arr)
    if isinstance(val, dict):
        return {k: deref(v, arr) for k, v in val.items()}
    if isinstance(val, list):
        return [deref(v, arr) for v in val]
    return val

for exec_id in [1811, 1810]:
    print(f'\n=== EXECUTION {exec_id} ===')
    cur.execute("SELECT data FROM execution_data WHERE executionId=?", (exec_id,))
    row = cur.fetchone()
    if not row:
        print('  no data'); continue

    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')

    outer = json.loads(raw)
    # outer is a list where elements reference each other by index
    resolved = deref(outer[0], outer)

    result = resolved.get('resultData', {})
    run_data = result.get('runData', {})

    print(f'  Last node: {result.get("lastNodeExecuted")}')
    print(f'  All nodes run: {list(run_data.keys())}')

    for node_name in ['Start Typing', 'Stop Typing', 'Typing2', 'Global Config']:
        if node_name in run_data:
            runs = run_data[node_name]
            run = runs[0] if runs else {}
            err = run.get('error')
            if err:
                print(f'  [{node_name}] ERROR: {str(err)[:200]}')
            else:
                try:
                    out_data = run.get('data', {}).get('main', [[]])[0]
                    first_item = out_data[0].get('json', {}) if out_data else {}
                    print(f'  [{node_name}] OK -> {str(first_item)[:200]}')
                except Exception as e:
                    print(f'  [{node_name}] OK (parse err: {e})')
        else:
            print(f'  [{node_name}] NOT RUN')

conn.close()
