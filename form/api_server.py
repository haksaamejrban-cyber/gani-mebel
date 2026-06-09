#!/usr/bin/env python3
import json
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests as req
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from db import get_connection, int_or_none

load_dotenv('/var/www/form/.env')


N8N_WEBHOOK = 'http://localhost:8080/webhook/9d81e8a9-8e6c-4d37-a161-40967a689f60'
# N8N_WEBHOOK = 'http://localhost:8080/webhook-test/9d81e8a9-8e6c-4d37-a161-40967a689f60'

def trigger_n8n(payload):
    def _clean(v):
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        if isinstance(v, str):
            return ''.join(c for c in v if ord(c) >= 32 or c in '\t')
        return v
    def _send():
        try:
            clean = {k: _clean(v) for k, v in payload.items()}
            req.post(N8N_WEBHOOK, json=clean, timeout=10)
        except Exception as e:
            print(f'n8n webhook error: {e}')
    threading.Thread(target=_send, daemon=True).start()

app = Flask(__name__)
CORS(app)


def normalize_to_mm(value):
    if value is None:
        return None
    try:
        v = float(str(value).strip().replace(',', '.'))
    except (ValueError, TypeError):
        return None
    if v <= 0:
        return None
    if v < 100:
        return int(round(v * 1000))   # метры → мм
    elif v < 1000:
        return int(round(v * 10))     # сантиметры → мм
    else:
        return int(round(v))          # уже мм

typing_sessions = {}
chat_sessions = {}  # chatId -> session_id
placeholder_sessions = {}  # session_id -> {chat_id, message_id, ...}

# Папки для резервного сохранения данных и фото
DATA_DIR = Path('/var/www/form/data')
PHOTOS_DIR = Path('/var/www/form/photos')
LOGS_FILE = Path('/var/www/form/submissions.json')

DATA_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(exist_ok=True)
(PHOTOS_DIR / 'wall').mkdir(exist_ok=True)
(PHOTOS_DIR / 'reference').mkdir(exist_ok=True)

if not LOGS_FILE.exists():
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)



def save_json_backup(session_id, payload):
    form_file = DATA_DIR / f"{session_id}.json"
    with open(form_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def backup_log(entry):
    with open(LOGS_FILE, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    logs.append(entry)
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def ensure_session_id_column():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM client_photos_new LIKE 'session_id'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE client_photos_new ADD COLUMN session_id VARCHAR(50) NULL AFTER name")
            conn.commit()


@app.route('/api/save-form', methods=['POST'])
def save_form():
    try:
        data = request.get_json() or {}
        session_id = str(uuid.uuid4())

        phone = str(data.get('userId') or data.get('phone') or 'unknown')
        name = str(data.get('userName') or data.get('user_name') or 'unknown')
        material = data.get('material', 'ЛДСП')
        color = data.get('color', 'не указан')
        hardware = data.get('hardware', 'Стандарт')
        panel = int(data.get('penal', '10') or '10')

        height_ceiling = bool(data.get('height_ceiling'))
        form_fields = dict(
            length=normalize_to_mm(data.get('length')),
            height=None if height_ceiling else (int_or_none(data.get('height')) or 10),
            height_ceiling=height_ceiling,
            material=material,
            color=color,
            sink_width=int_or_none(data.get('sink')),
            stove_width=int_or_none(data.get('stove')),
            oven_width=int_or_none(data.get('oven')),
            dishwasher_width=int_or_none(data.get('dishwasher')),
            microwave_width=int_or_none(data.get('microwave')),
            hood_width=int_or_none(data.get('hood')),
            fridge_height=int_or_none(data.get('fridge')),
            panel=panel,
            furniture_type=hardware,
        )

        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM client_photos_new WHERE phone = %s AND stage = 'collecting' ORDER BY last_update DESC LIMIT 1",
                (phone,)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE client_photos_new SET
                        length=%(length)s, height=%(height)s, height_ceiling=%(height_ceiling)s,
                        material=%(material)s, color=%(color)s,
                        sink_width=%(sink_width)s, stove_width=%(stove_width)s,
                        oven_width=%(oven_width)s, dishwasher_width=%(dishwasher_width)s,
                        microwave_width=%(microwave_width)s, hood_width=%(hood_width)s,
                        fridge_height=%(fridge_height)s, panel=%(panel)s,
                        furniture_type=%(furniture_type)s, last_update=CURRENT_TIMESTAMP
                    WHERE id=%(id)s
                """, {**form_fields, 'id': existing['id']})
                conn.commit()
                inserted_id = existing['id']
            else:
                cursor.execute(
                    "INSERT INTO client_photos_new (phone, stage, status, name) VALUES (%s, %s, %s, %s)",
                    (phone, 'collecting', 'collecting', 'Кухня')
                )
                conn.commit()
                inserted_id = cursor.lastrowid
                cursor.execute("""
                    UPDATE client_photos_new SET
                        length=%(length)s, height=%(height)s, height_ceiling=%(height_ceiling)s,
                        material=%(material)s, color=%(color)s,
                        sink_width=%(sink_width)s, stove_width=%(stove_width)s,
                        oven_width=%(oven_width)s, dishwasher_width=%(dishwasher_width)s,
                        microwave_width=%(microwave_width)s, hood_width=%(hood_width)s,
                        fridge_height=%(fridge_height)s, panel=%(panel)s,
                        furniture_type=%(furniture_type)s, last_update=CURRENT_TIMESTAMP
                    WHERE id=%(id)s
                """, {**form_fields, 'id': inserted_id})
                conn.commit()

        save_json_backup(session_id, {
            'sessionId': session_id,
            'data': data,
            'createdAt': datetime.now().isoformat(),
            'wallPhotoPath': None,
            'referencePhotoPath': None,
        })

        backup_log({
            'sessionId': session_id,
            'userId': data.get('userId'),
            'timestamp': datetime.now().isoformat(),
            'status': 'form_submitted',
        })

        return jsonify({
            'success': True,
            'sessionId': session_id,
            'clientId': inserted_id,
            'message': 'Данные формы сохранены в client_photos_new'
        }), 200

    except Exception as e:
        print(f"Ошибка при сохранении формы: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    try:
        client_id = request.form.get('clientId')
        photo_type = request.form.get('type')
        photo_file = request.files.get('photo')

        if not client_id or not photo_file or photo_type not in ('wall', 'reference'):
            return jsonify({'success': False, 'error': 'Отсутствуют обязательные параметры'}), 400

        file_ext = os.path.splitext(photo_file.filename)[1]
        filename = f"{client_id}_{photo_type}{file_ext}"
        filepath = PHOTOS_DIR / photo_type / filename
        photo_file.save(str(filepath))

        field_name = 'wall_photo_url' if photo_type == 'wall' else 'ref_photo_url'
        photo_url = f"/photos/{photo_type}/{filename}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE client_photos_new SET {field_name} = %s, last_update = CURRENT_TIMESTAMP WHERE id = %s",
                (photo_url, client_id)
            )
            conn.commit()

        backup_log({
            'clientId': client_id,
            'timestamp': datetime.now().isoformat(),
            'photoUploaded': photo_type,
        })

        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM client_photos_new WHERE id = %s",
                (client_id,)
            )
            row = cursor.fetchone()
        if row and row.get('wall_photo_url') and row.get('ref_photo_url'):
            trigger_n8n(row)

        return jsonify({'success': True, 'message': f'Фото {photo_type} загружено', 'filename': filename}), 200

    except Exception as e:
        print(f"Ошибка при загрузке фото: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/faq-defaults', methods=['GET'])
def faq_defaults():
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT id, question, answer, category, keywords FROM faq_new ORDER BY id')
            faq_items = cursor.fetchall()
        return jsonify({'success': True, 'items': faq_items}), 200
    except Exception as e:
        print(f"Ошибка при получении FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


MAX_TYPING_SECONDS = 80


def typing_loop(chat_id: str, session_id: str, instance_id: str, api_token: str, host_prefix: str):
    url = f"https://{host_prefix}.api.greenapi.com/waInstance{instance_id}/sendTyping/{api_token}"
    print(f"[Typing] Старт для {chat_id}")
    started_at = time.time()
    while typing_sessions.get(session_id, False):
        if time.time() - started_at > MAX_TYPING_SECONDS:
            print(f"[Typing] Таймаут {MAX_TYPING_SECONDS}с, авто-стоп")
            break
        try:
            req.post(url, json={"chatId": chat_id, "typingTime": 10000}, timeout=15)
        except Exception as e:
            print(f"[Typing] Ошибка: {e}")
        time.sleep(8)
    typing_sessions.pop(session_id, None)
    chat_sessions.pop(chat_id, None)
    print(f"[Typing] Остановлен для {chat_id}")


@app.route('/api/start-typing', methods=['POST'])
def start_typing():
    try:
        data = request.get_json() or {}
        chat_id = data.get('chatId')

        if not chat_id:
            return jsonify({'success': False, 'error': 'chatId обязателен'}), 400

        instance_id = data.get('instanceId') or os.getenv("GREEN_API_INSTANCE_ID")
        api_token = data.get('apiToken') or os.getenv("GREEN_API_TOKEN")
        host_prefix = data.get('hostPrefix') or os.getenv("GREEN_API_HOST_PREFIX")

        old_session = chat_sessions.get(chat_id)
        if old_session:
            typing_sessions[old_session] = False

        session_id = str(uuid.uuid4())
        typing_sessions[session_id] = True
        chat_sessions[chat_id] = session_id

        threading.Thread(target=typing_loop, args=(chat_id, session_id, instance_id, api_token, host_prefix), daemon=True).start()

        print(f"[Typing] Запущен для {chat_id}, session={session_id}")
        return jsonify({'success': True, 'session_id': session_id, 'chat_id': chat_id}), 200

    except Exception as e:
        print(f"[Typing] Ошибка start_typing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stop-typing', methods=['POST'])
def stop_typing():
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        chat_id = data.get('chatId')

        if not session_id and chat_id:
            session_id = chat_sessions.get(chat_id)

        if not session_id:
            return jsonify({'success': False, 'error': 'session_id или chatId обязателен'}), 400

        if session_id not in typing_sessions:
            return jsonify({'success': True, 'status': 'not_active', 'session_id': session_id}), 200

        typing_sessions[session_id] = False
        print(f"[Typing] Остановка {session_id}")
        return jsonify({'success': True, 'status': 'stopped', 'session_id': session_id}), 200

    except Exception as e:
        print(f"[Typing] Ошибка stop_typing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/is-typing', methods=['POST'])
def is_typing():
    try:
        data = request.get_json() or {}
        chat_id = data.get('chatId')

        if not chat_id:
            return jsonify({'success': False, 'error': 'chatId обязателен'}), 400

        session_id = chat_sessions.get(chat_id)
        active = bool(session_id and typing_sessions.get(session_id))
        return jsonify({'success': True, 'active': active, 'session_id': session_id}), 200

    except Exception as e:
        print(f"[Typing] Ошибка is_typing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/save-message', methods=['POST'])
def save_message():
    try:
        data = request.get_json() or {}
        phone = str(data.get('phone') or data.get('client_phone') or '')
        user_name = str(data.get('user_name') or data.get('userName') or '')
        message_text = str(data.get('message_text') or data.get('message') or '')
        bot_reply = str(data.get('bot_reply') or data.get('reply') or '')

        if not phone or not message_text:
            return jsonify({'success': False, 'error': 'phone и message_text обязательны'}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO messages_new
                   (client_phone, user_name, message_text, message_type, bot_reply, bot_reply_type)
                   VALUES (%s, %s, %s, 'text', %s, 'text')""",
                (phone, user_name, message_text, bot_reply)
            )
            conn.commit()
            inserted_id = cursor.lastrowid

        return jsonify({'success': True, 'id': inserted_id}), 200

    except Exception as e:
        print(f"Ошибка save_message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    print('Сервер запускается на http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
