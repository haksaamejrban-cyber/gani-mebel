import requests, time

instance_id = "7107613930"
api_token = "b3e50a7379984b9f9bce74d012d77bbc07eb3a8924434a5a8d"
host_prefix = "7107"
chat_id = "77054901431@c.us"
base = f"https://{host_prefix}.api.greenapi.com/waInstance{instance_id}"

# 1. Send placeholder
r = requests.post(f"{base}/sendMessage/{api_token}", json={
    "chatId": chat_id,
    "message": "⏳"
}, timeout=10)
print(f"Send placeholder: {r.status_code} {r.text}")
data = r.json()
msg_id = data.get("idMessage")
print(f"Message ID: {msg_id}")

time.sleep(3)

# 2. Try to delete it
if msg_id:
    r2 = requests.post(f"{base}/deleteMessage/{api_token}", json={
        "chatId": chat_id,
        "idMessage": msg_id
    }, timeout=10)
    print(f"Delete message: {r2.status_code} {r2.text}")
