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

app = Flask(__name__)
CORS(app)

typing_sessions = {}

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

        form_fields = dict(
            session_id=session_id,
            length=int_or_none(data.get('length')),
            height=int_or_none(data.get('height')),
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

        ensure_session_id_column()
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM client_photos_new WHERE phone = %s AND stage = 'completed' ORDER BY last_update DESC LIMIT 1",
                (phone,)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE client_photos_new SET
                        session_id=%(session_id)s, length=%(length)s, height=%(height)s,
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
                        session_id=%(session_id)s, length=%(length)s, height=%(height)s,
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
        session_id = request.form.get('sessionId')
        photo_type = request.form.get('type')
        photo_file = request.files.get('photo')

        if not session_id or not photo_file or photo_type not in ('wall', 'reference'):
            return jsonify({'success': False, 'error': 'Отсутствуют обязательные параметры'}), 400

        file_ext = os.path.splitext(photo_file.filename)[1]
        filename = f"{session_id}_{photo_type}{file_ext}"
        filepath = PHOTOS_DIR / photo_type / filename
        photo_file.save(str(filepath))

        field_name = 'wall_photo_url' if photo_type == 'wall' else 'ref_photo_url'
        photo_url = f"/photos/{photo_type}/{filename}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE client_photos_new SET {field_name} = %s, last_update = CURRENT_TIMESTAMP WHERE session_id = %s",
                (photo_url, session_id)
            )
            conn.commit()

        # обновляем резервный JSON, если существует
        form_file = DATA_DIR / f"{session_id}.json"
        if form_file.exists():
            with open(form_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            if photo_type == 'wall':
                session_data['wallPhotoPath'] = photo_url
            else:
                session_data['referencePhotoPath'] = photo_url
            session_data['updatedAt'] = datetime.now().isoformat()
            with open(form_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

        backup_log({
            'sessionId': session_id,
            'timestamp': datetime.now().isoformat(),
            'photoUploaded': photo_type,
        })

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


def typing_loop(chat_id: str, session_id: str):
    host_prefix = os.getenv("GREEN_API_HOST_PREFIX")
    instance_id = os.getenv("GREEN_API_INSTANCE_ID")
    api_token = os.getenv("GREEN_API_TOKEN")
    url = f"https://{host_prefix}.api.greenapi.com/waInstance{instance_id}/sendTyping/{api_token}"

    print(f"[Typing] Старт сессии {session_id} для чата {chat_id}")
    while typing_sessions.get(session_id, False):
        try:
            resp = req.post(url, json={"chatId": chat_id, "typingTime": 5000}, timeout=5)
            print(f"[Typing] Сигнал для {chat_id}, статус: {resp.status_code}")
        except Exception as e:
            print(f"[Typing] Ошибка запроса: {e}")
        time.sleep(4)

    print(f"[Typing] Сессия {session_id} остановлена")
    typing_sessions.pop(session_id, None)


@app.route('/api/start-typing', methods=['POST'])
def start_typing():
    try:
        data = request.get_json() or {}
        chat_id = data.get('chatId')

        if not chat_id:
            return jsonify({'success': False, 'error': 'chatId обязателен'}), 400

        session_id = str(uuid.uuid4())
        typing_sessions[session_id] = True

        thread = threading.Thread(target=typing_loop, args=(chat_id, session_id), daemon=True)
        thread.start()

        print(f"[Typing] Запущен поток для чата {chat_id}, session_id: {session_id}")
        return jsonify({'success': True, 'session_id': session_id, 'chat_id': chat_id}), 200

    except Exception as e:
        print(f"[Typing] Ошибка start_typing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stop-typing', methods=['POST'])
def stop_typing():
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({'success': False, 'error': 'session_id обязателен'}), 400

        typing_sessions[session_id] = False
        print(f"[Typing] Остановка сессии {session_id}")
        return jsonify({'success': True, 'status': 'stopped', 'session_id': session_id}), 200

    except Exception as e:
        print(f"[Typing] Ошибка stop_typing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    print('Сервер запускается на http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
