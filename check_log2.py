import paramiko

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

# Check actual file size and recent content
cmds = [
    'wc -l /var/log/api_server.log',
    'ls -la /var/log/api_server.log',
    'grep -a "start-typing\|Старт\|Start" /var/log/api_server.log | tail -10',
    'grep -a "api_server\|5000\|start" /var/log/api_server.log | tail -10',
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(f'>>> {cmd[:70]}')
    if out: print(out[:500])
    if err: print('ERR:', err[:200])

client.close()
