import paramiko

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

cmds = [
    'ps aux | grep api_server | grep -v grep',
    'ls -la /proc/$(pgrep -f api_server.py)/fd 2>/dev/null | grep -v "^total"',
    'ls -la /var/log/api_server* 2>/dev/null',
    'find /var /tmp -name "*.log" -newer /var/log/api_server.log 2>/dev/null | head -10',
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    print(f'>>> {cmd[:80]}')
    print(out[:600])

client.close()
