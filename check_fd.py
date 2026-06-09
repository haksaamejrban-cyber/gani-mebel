import paramiko

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

cmds = [
    'ls -la /proc/2265699/fd/1 /proc/2265699/fd/2 2>/dev/null',
    'readlink /proc/2265699/fd/1 2>/dev/null',
    'readlink /proc/2265699/fd/2 2>/dev/null',
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    print(f'>>> {cmd}')
    print(out)

client.close()
