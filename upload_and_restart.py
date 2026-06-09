import paramiko, time

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

sftp = client.open_sftp()
sftp.put(r'D:\Project Gani Mebel\form\kitchen\index.html', '/var/www/form/kitchen/index.html')
sftp.put(r'D:\Project Gani Mebel\form\kitchen\index.html', '/var/www/form/form/kitchen/index.html')
sftp.put(r'D:\Project Gani Mebel\api_server.py', '/var/www/form/api_server.py')
sftp.close()
print("Files uploaded")

# Restart api_server
stdin, stdout, stderr = client.exec_command("pkill -f api_server.py; sleep 1; cd /var/www/form && nohup python3 api_server.py > /var/log/api_server.log 2>&1 & echo $!")
time.sleep(2)
print("api_server restarted, PID:", stdout.read().decode().strip())

# Verify
stdin2, stdout2, stderr2 = client.exec_command("ps aux | grep api_server.py | grep -v grep")
print("Running:", stdout2.read().decode().strip())

client.close()
