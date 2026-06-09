content = open('/var/www/form/api_server.py').read()

old1 = "                conn.commit()\n                inserted_id = existing['id']\n            else:"
new1 = "                conn.commit()\n                inserted_id = existing['id']\n                trigger_n8n({**form_fields, 'phone': phone, 'clientId': inserted_id})\n            else:"
content = content.replace(old1, new1)

old2 = "                \"\"\", {**form_fields, 'id': inserted_id})\n                conn.commit()\n\n        save_json_backup"
new2 = "                \"\"\", {**form_fields, 'id': inserted_id})\n                conn.commit()\n                trigger_n8n({**form_fields, 'phone': phone, 'clientId': inserted_id})\n\n        save_json_backup"
content = content.replace(old2, new2)

open('/var/www/form/api_server.py', 'w').write(content)
print('Done. trigger_n8n calls:', content.count('trigger_n8n('))
