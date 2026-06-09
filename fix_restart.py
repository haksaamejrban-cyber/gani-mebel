import paramiko, time

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

cmds = [
    'ss -tlnp | grep 5000',
    'ps aux | grep api_server | grep -v grep',
    'systemctl list-units | grep api',
    'ls /etc/supervisor/conf.d/ 2>/dev/null || echo no supervisor',
    'cat /etc/systemd/system/api*.service 2>/dev/null || echo no systemd service',
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    print(f'>>> {cmd}')
    print(out[:400])

client.close()
