import paramiko, time

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

stdin, stdout, stderr = client.exec_command("cd /var/www/form && nohup python3 api_server.py >> /var/log/api_server.log 2>&1 &")
time.sleep(3)

stdin2, stdout2, stderr2 = client.exec_command("ps aux | grep api_server.py | grep -v grep")
print("Processes:", stdout2.read().decode())

stdin3, stdout3, stderr3 = client.exec_command("tail -20 /var/log/api_server.log")
print("Log:", stdout3.read().decode())

client.close()
