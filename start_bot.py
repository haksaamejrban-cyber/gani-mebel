import paramiko, time, sys

def out(text):
    sys.stdout.buffer.write(text.encode('utf-8'))
    sys.stdout.buffer.write(b'\n')
    sys.stdout.buffer.flush()

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

client.exec_command("pkill -f bot.py")
time.sleep(2)
client.exec_command("cd /var/www/form && nohup python3 bot.py >> /var/log/bot.log 2>&1 &")
time.sleep(3)

stdin, stdout, _ = client.exec_command("ps aux | grep bot.py | grep -v grep")
proc = stdout.read().decode('utf-8', errors='replace').strip()
out("Process: " + (proc if proc else "not found"))

stdin2, stdout2, _ = client.exec_command("tail -10 /var/log/bot.log")
log = stdout2.read().decode('utf-8', errors='replace')
out("Log:\n" + log)

client.close()
