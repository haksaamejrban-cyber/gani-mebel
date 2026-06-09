import sys
sys.path.insert(0, r'D:\Project Gani Mebel')
import ssh_helper

# Write a script to the server, run it, get output as file
script = """
import sys, json
sys.path.insert(0, '/var/www/form')
from db import get_connection
conn = get_connection()
c = conn.cursor(dictionary=True)
c.execute("SELECT * FROM faq_new")
rows = c.fetchall()
conn.close()
with open('/tmp/faq_out.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, default=str)
print("done")
"""

import paramiko
HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

sftp = client.open_sftp()
with sftp.open('/tmp/query_faq.py', 'w') as f:
    f.write(script.encode('utf-8'))

stdin, stdout, stderr = client.exec_command('python3 /tmp/query_faq.py')
print(stdout.read().decode())

sftp.get('/tmp/faq_out.json', r'D:\Project Gani Mebel\faq_out.json')
sftp.close()
client.close()
print("Downloaded faq_out.json")
