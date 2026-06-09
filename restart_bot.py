import paramiko, time

HOST = '188.244.115.68'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='root', password='a7rnS$NBZ#ph', timeout=10)

stdin, stdout, stderr = client.exec_command("pkill -f bot.py; sleep 1; cd /var/www/form && nohup python3 bot.py >> /var/log/bot.log 2>&1 &")
time.sleep(2)

stdin2, stdout2, _ = client.exec_command("ps aux | grep bot.py | grep -v grep")
print("Bot:", stdout2.read().decode().strip())
client.close()
