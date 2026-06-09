content = open('/var/www/form/api_server.py').read()

# Добавить import requests
if 'import requests' not in content:
    content = content.replace('from flask import', 'import requests\nfrom flask import')

# Добавить N8N функцию перед app = Flask
n8n_block = """
N8N_WEBHOOK = 'http://localhost:8080/webhook/9d81e8a9-8e6c-4d37-a161-40967a689f60'
# N8N_WEBHOOK = 'http://localhost:8080/webhook-test/9d81e8a9-8e6c-4d37-a161-40967a689f60'

def trigger_n8n(payload):
    try:
        requests.post(N8N_WEBHOOK, json=payload, timeout=10)
    except Exception as e:
        print(f'n8n webhook error: {e}')

"""
if 'N8N_WEBHOOK' not in content:
    content = content.replace('app = Flask(__name__)', n8n_block + 'app = Flask(__name__)')

# Вызов n8n после UPDATE при найденной записи
old1 = "                conn.commit()\n                inserted_id = existing['id']\n            else:"
new1 = "                conn.commit()\n                inserted_id = existing['id']\n                trigger_n8n({**form_fields, 'phone': phone, 'clientId': inserted_id})\n            else:"
if "trigger_n8n" not in content:
    content = content.replace(old1, new1)

    # Вызов n8n после UPDATE при новой записи
    old2 = "                conn.commit()\n\n        save_json_backup"
    new2 = "                conn.commit()\n                trigger_n8n({**form_fields, 'phone': phone, 'clientId': inserted_id})\n\n        save_json_backup"
    content = content.replace(old2, new2)

open('/var/www/form/api_server.py', 'w').write(content)
print('Done. n8n calls:', content.count('trigger_n8n'))
