import sqlite3, json

db = '/var/lib/docker/rootfs/overlayfs/dbe669259895decef5624b661d1ee946727ca5393ca693282fcea06780e6152f/home/node/.n8n/database.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Last 5 executions of AI_Assist_Gani
cur.execute("""
    SELECT e.id, e.startedAt, e.stoppedAt, e.status, e.finished
    FROM execution_entity e
    WHERE e.workflowId = 'KNTaJvjMpXXpIHmf'
    ORDER BY e.startedAt DESC
    LIMIT 5
""")
print('=== LAST EXECUTIONS ===')
execs = cur.fetchall()
for ex in execs:
    print(f"id={ex[0]}, start={ex[1]}, stop={ex[2]}, status={ex[3]}, finished={ex[4]}")

# Get the last execution data to see which nodes ran
if execs:
    last_id = execs[0][0]
    cur.execute("SELECT data FROM execution_data WHERE executionId=?", (last_id,))
    row = cur.fetchone()
    if row:
        try:
            data = json.loads(row[0])
            result_data = data.get('resultData', {})
            run_data = result_data.get('runData', {})
            print(f'\n=== NODES RAN IN LAST EXECUTION (id={last_id}) ===')
            for node_name, runs in run_data.items():
                for run in runs:
                    error = run.get('error')
                    status = 'OK' if not error else f'ERROR: {error.get("message","?")[:100]}'
                    print(f"  {node_name}: {status}")
        except Exception as e:
            print(f'Parse error: {e}')

conn.close()
