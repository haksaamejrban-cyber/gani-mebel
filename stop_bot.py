import paramiko, sys

def out(text):
    sys.stdout.buffer.write(text.encode('utf-8'))
    sys.stdout.buffer.write(b'\n')
    sys.stdout.buffer.flush()

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

stdin, stdout, _ = client.exec_command("pkill -9 -f bot.py; sleep 1; ps aux | grep bot.py | grep -v grep")
result = stdout.read().decode('utf-8', errors='replace').strip()
out("Bot stopped" if not result else "Still running: " + result)

client.close()
