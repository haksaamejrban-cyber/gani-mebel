import requests

resp1 = requests.get(
    'https://7107.api.greenapi.com/waInstance7107613930/getStateInstance/b3e50a7379984b9f9bce74d012d77bbc07eb3a8924434a5a8d',
    timeout=10
)
print('n8n instance state:', resp1.status_code, resp1.text[:200])

resp2 = requests.post(
    'https://7107.api.greenapi.com/waInstance7107613930/sendTyping/b3e50a7379984b9f9bce74d012d77bbc07eb3a8924434a5a8d',
    json={'chatId': '77478409748@c.us', 'typingTime': 5000},
    timeout=10
)
print('sendTyping n8n creds:', resp2.status_code, resp2.text[:200])
