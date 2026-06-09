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
# runData is at index 5
run_data = outer[5]
print(f'runData keys: {list(run_data.keys())}')

# Check typing nodes specifically
for key in run_data:
    if any(x in key.lower() for x in ['typing', 'config', 'start', 'stop']):
        val = run_data[key]
        # Each node run is a list of run attempts
        if isinstance(val, list) and val:
            run = val[0]
            if isinstance(run, str):
                run = outer[int(run)]  # dereference
            err = run.get('error') if isinstance(run, dict) else None
            print(f'\n  [{key}]')
            if err:
                print(f'    ERROR: {str(err)[:200]}')
            else:
                try:
                    data_obj = run.get('data', {})
                    main = data_obj.get('main', [[]])
                    if main and main[0]:
                        first = main[0][0] if isinstance(main[0], list) else main[0]
                        if isinstance(first, str):
                            first = outer[int(first)]
                        j = first.get('json', {}) if isinstance(first, dict) else {}
                        print(f'    OK, json: {str(j)[:200]}')
                    else:
                        print(f'    OK (empty output)')
                except Exception as e:
                    print(f'    OK (err reading output: {e})')
        else:
            print(f'\n  [{key}] val type: {type(val)}')

conn.close()
