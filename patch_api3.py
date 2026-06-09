content = open('/var/www/form/api_server.py').read()

# 1. Убрать trigger_n8n из save_form
content = content.replace(
    "                trigger_n8n({'client_phone': phone, 'clientId': inserted_id})\n            else:",
    "            else:"
)
content = content.replace(
    "                trigger_n8n({'client_phone': phone, 'clientId': inserted_id})\n\n        save_json_backup",
    "\n        save_json_backup"
)

# 2. Добавить trigger_n8n в upload-photo после reference
old = "        return jsonify({'success': True, 'message': f'Фото {photo_type} загружено', 'filename': filename}), 200"
new = """        if photo_type == 'reference':
            try:
                with get_connection() as conn2:
                    cur2 = conn2.cursor(dictionary=True)
                    cur2.execute("SELECT phone FROM client_photos_new WHERE session_id = %s", (session_id,))
                    row = cur2.fetchone()
                if row:
                    trigger_n8n({'client_phone': row['phone']})
            except Exception as ne:
                print(f'n8n trigger error: {ne}')

        return jsonify({'success': True, 'message': f'Фото {photo_type} загружено', 'filename': filename}), 200"""
content = content.replace(old, new)

# 3. Добавить /api/complete endpoint перед /api/faq-defaults
complete_endpoint = """
@app.route('/api/complete', methods=['POST'])
def complete():
    try:
        data = request.get_json() or {}
        session_id = data.get('sessionId')
        if session_id:
            with get_connection() as conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT phone FROM client_photos_new WHERE session_id = %s", (session_id,))
                row = cur.fetchone()
            if row:
                trigger_n8n({'client_phone': row['phone']})
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f'complete error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


"""
content = content.replace("@app.route('/api/faq-defaults'", complete_endpoint + "@app.route('/api/faq-defaults'")

open('/var/www/form/api_server.py', 'w').write(content)
print('Done. trigger_n8n calls:', content.count('trigger_n8n('))
