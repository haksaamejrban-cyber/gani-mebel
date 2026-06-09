import requests

instance_id = "7107613930"
api_token = "b3e50a7379984b9f9bce74d012d77bbc07eb3a8924434a5a8d"
host_prefix = "7107"
chat_id = "77054901431@c.us"

url = f"https://{host_prefix}.api.greenapi.com/waInstance{instance_id}/sendTyping/{api_token}"

# Test 1: typingType typing
r1 = requests.post(url, json={"chatId": chat_id, "typingTime": 5000, "typingType": "typing"}, timeout=10)
print(f"typingType=typing: {r1.status_code} {r1.text}")

# Test 2: no typingType
r2 = requests.post(url, json={"chatId": chat_id, "typingTime": 5000}, timeout=10)
print(f"no typingType: {r2.status_code} {r2.text}")

# Test 3: check what params GreenAPI accepts
r3 = requests.post(url, json={"chatId": chat_id, "typingTime": 5000, "typingType": "composing"}, timeout=10)
print(f"typingType=composing: {r3.status_code} {r3.text}")
