import paramiko

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

cmds = [
    'curl -s -X POST http://localhost:5000/api/is-typing -H "Content-Type: application/json" -d \'{"chatId":"77478409748@c.us"}\'',
    'curl -s -X POST http://localhost:5000/api/is-typing -H "Content-Type: application/json" -d \'{"chatId":"test@c.us"}\'',
    'tail -20 /var/log/api_server.log',
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    print('>>>', cmd[:60])
    print(stdout.read().decode('utf-8', errors='replace'))

client.close()
