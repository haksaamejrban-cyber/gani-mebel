import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Check last executions - look for errors
cur.execute("""
    SELECT e.id, e.startedAt, e.stoppedAt, e.status
    FROM execution_entity e
    WHERE e.workflowId = 'KNTaJvjMpXXpIHmf'
    ORDER BY e.startedAt DESC
    LIMIT 10
""")
execs = cur.fetchall()
for ex in execs:
    print(f"id={ex[0]}, start={ex[1]}, status={ex[3]}")

# Parse execution data correctly
last_id = execs[0][0]
cur.execute("SELECT data FROM execution_data WHERE executionId=?", (last_id,))
row = cur.fetchone()
if row:
    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    data = json.loads(raw)

    # n8n stores as list sometimes
    if isinstance(data, list):
        data = data[0] if data else {}

    print(f'\n=== DATA KEYS: {list(data.keys())} ===')
    result = data.get('resultData') or data.get('data', {})
    if isinstance(result, dict):
        run_data = result.get('runData', {})
        print(f'\n=== NODES RAN (id={last_id}) ===')
        for node_name, runs in run_data.items():
            try:
                run = runs[0] if runs else {}
                error = run.get('error')
                output_items = run.get('data', {}).get('main', [[]])[0] if not error else []
                status = 'OK' if not error else f'ERROR: {str(error)[:150]}'
                print(f"  [{status}] {node_name}")
            except Exception as e:
                print(f"  [PARSE ERR] {node_name}: {e}")
    else:
        print(f'result type: {type(result)}')
        print(str(result)[:500])

conn.close()
