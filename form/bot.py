import logging
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio
import time
from db import get_connection
# Настройки
BOT_TOKEN = "8744155349:AAGrwDzidyM_5lJ5OCNBKg2wwZVhBeATN7o"
FORM_URL = f"https://form.ganimebel.kz/kitchen/?v=4&t={int(time.time())}"
LOG_FILE = "/var/www/form/bot_logs.json"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_message_to_db(client_phone, user_name, message_text, message_type='user', bot_reply=None, bot_reply_type=None):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages_new (client_phone, user_name, message_text, message_type, bot_reply, bot_reply_type) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    str(client_phone),
                    user_name,
                    message_text,
                    message_type,
                    bot_reply,
                    bot_reply_type,
                )
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при записи сообщения в БД: {e}")


# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def log_data(user_id, user_name, data):
    """Логирует данные формы в JSON файл"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "user_name": user_name,
            "data": json.loads(data) if isinstance(data, str) else data
        }
        
        try:
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        logs.append(log_entry)
        
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Данные сохранены для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при логировании: {e}")

@dp.message(Command("start"))
async def start(message: types.Message):
    """Обработчик команды /start"""
    
    # Генерируем уникальный URL для обхода кэша
    unique_url = f"https://form.ganimebel.kz/kitchen/?v=5&t={int(time.time())}&u={message.from_user.id}"
    
    # Клавиатура с кнопкой WebApp
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="📐 Открыть конфигуратор кухни",
                web_app=WebAppInfo(url=unique_url)
            )
        ]]
    )
    
    await message.answer(
        "🍳 Добро пожаловать в Gani Mebel!\n\n"
        "Нажмите кнопку ниже, чтобы начать конфигурацию вашей кухни:",
        reply_markup=keyboard
    )
    log_message_to_db(message.from_user.id, message.from_user.full_name, message.text or '/start', 'user', 'Отправлена кнопка открытия формы', 'bot')

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать конфигурацию кухни\n"
        "/update - Принудительно обновить форму\n"
        "/help - Эта справка\n"
        "/status - Статус бота\n\n"
        "Просто нажмите на кнопку ниже и заполните форму!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="📐 Конфигуратор кухни",
                    web_app=WebAppInfo(url=f"https://form.ganimebel.kz/kitchen/?v=7&t={int(time.time())}&u={message.from_user.id}")
                )
            ]]
        )
    )
    log_message_to_db(message.from_user.id, message.from_user.full_name, message.text or '/help', 'user', 'Отправлена справка и ссылка на форму', 'bot')

@dp.message(Command("status"))
async def status(message: types.Message):
    """Обработчик команды /status"""
    await message.answer("✅ Бот активен и готов к работе!")
    log_message_to_db(message.from_user.id, message.from_user.full_name, message.text or '/status', 'user', 'Проверка статуса бота', 'bot')

@dp.message(Command("update"))
async def update(message: types.Message):
    """Обработчик команды /update для принудительного обновления формы"""
    
    # Генерируем уникальный URL для обхода кэша
    unique_url = f"https://form.ganimebel.kz/kitchen/?v=6&t={int(time.time())}&u={message.from_user.id}&force=1"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🔄 Открыть обновленную форму",
                web_app=WebAppInfo(url=unique_url)
            )
        ]]
    )
    
    await message.answer(
        "🔄 Форма обновлена!\n\n"
        "Нажмите кнопку ниже для открытия свежей версии:",
        reply_markup=keyboard
    )
    log_message_to_db(message.from_user.id, message.from_user.full_name, message.text or '/update', 'user', 'Отправлена команда обновления формы', 'bot')

@dp.message()
async def handle_web_app_data(message: types.Message):
    """Обработчик данных с WebApp формы и текстовых сообщений"""
    if message.text and not message.web_app_data:
        log_message_to_db(message.from_user.id, message.from_user.full_name, message.text, 'user', None, None)
        return

    if message.web_app_data:
        data = message.web_app_data.data
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        
        logger.info(f"Получены данные от {user_name} ({user_id}): {data}")
        
        # Логируем данные в файл и в базу
        log_data(user_id, user_name, data)
        log_message_to_db(user_id, user_name, json.dumps(data, ensure_ascii=False), 'user', 'Данные формы получены', 'bot')
        
        # Отправляем подтверждение
        await message.answer(
            "✅ Спасибо! Ваши данные получены и сохранены.\n"
            "Наш специалист свяжется с вами в ближайшее время!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="📐 Заполнить заново",
                        web_app=WebAppInfo(url=FORM_URL)
                    )
                ]]
            )
        )

async def main():
    """Запуск бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
