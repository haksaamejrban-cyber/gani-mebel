import paramiko, json

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

script = """
import sys, json
sys.path.insert(0, '/var/www/form')
from db import get_connection
conn = get_connection()
c = conn.cursor(dictionary=True)
c.execute("DESCRIBE client_photos_new")
rows = c.fetchall()
conn.close()
with open('/tmp/table_out.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, default=str)
print("done")
"""

sftp = client.open_sftp()
with sftp.open('/tmp/query_table.py', 'w') as f:
    f.write(script.encode('utf-8'))

stdin, stdout, stderr = client.exec_command('python3 /tmp/query_table.py')
print(stdout.read().decode())
err = stderr.read().decode()
if err: print("ERR:", err)

sftp.get('/tmp/table_out.json', r'D:\Project Gani Mebel\table_out.json')
sftp.close()
client.close()
print("Downloaded")
