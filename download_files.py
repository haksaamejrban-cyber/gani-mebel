import paramiko

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

sftp = client.open_sftp()
sftp.get('/var/www/form/kitchen/index.html', r'D:\Project Gani Mebel\form\kitchen\index.html')
sftp.get('/var/www/form/api_server.py', r'D:\Project Gani Mebel\api_server.py')
sftp.close()
client.close()
print("Downloaded both files")
