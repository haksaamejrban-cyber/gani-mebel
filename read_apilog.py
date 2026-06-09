import paramiko

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

stdin, stdout, stderr = client.exec_command('tail -60 /var/www/form/api.log')
out = stdout.read().decode('utf-8', errors='replace')
client.close()

with open(r'D:\Project Gani Mebel\api_log.txt', 'w', encoding='utf-8') as f:
    f.write(out)
print('done')
