import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

for exec_id in [1811, 1810, 1809]:
    print(f'\n=== EXECUTION {exec_id} ===')
    cur.execute("SELECT data FROM execution_data WHERE executionId=?", (exec_id,))
    row = cur.fetchone()
    if not row:
        print('  no data')
        continue

    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')

    try:
        outer = json.loads(raw)
        # n8n wraps execution data
        if isinstance(outer, list):
            outer = outer[0]

        result = outer.get('resultData', {})
        if isinstance(result, str):
            # might be stringified JSON
            result = json.loads(result)

        run_data = result.get('runData', {})
        print(f'  Nodes executed: {list(run_data.keys())}')

        for node_name in ['Start Typing', 'Stop Typing', 'Typing2', 'Global Config']:
            if node_name in run_data:
                runs = run_data[node_name]
                run = runs[0] if runs else {}
                err = run.get('error')
                if err:
                    print(f'  [{node_name}] ERROR: {str(err)[:200]}')
                else:
                    # Try to get output
                    try:
                        out_data = run.get('data', {}).get('main', [[]])[0]
                        if out_data:
                            first_item = out_data[0].get('json', {})
                            print(f'  [{node_name}] OK, output: {str(first_item)[:150]}')
                        else:
                            print(f'  [{node_name}] OK (no output items)')
                    except:
                        print(f'  [{node_name}] OK')
            else:
                print(f'  [{node_name}] NOT RUN')
    except Exception as e:
        print(f'  Parse error: {e}')
        print(f'  Raw start: {str(raw)[:200]}')

conn.close()
