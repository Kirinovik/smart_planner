# main.py

import telebot
import os
from dotenv import load_dotenv
import json

# --- 1. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
# Должна быть выполнена первой, чтобы os.getenv() работала
load_dotenv()

# --- 2. ИНИЦИАЛИЗАЦИЯ TELEGRAM И POSTGRES (ДО ИМПОРТА АГЕНТОВ/HANDLER) ---

# Получение токена Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Токен Telegram не найден! Проверьте файл .env")
    exit()

# Инициализация объекта 'bot' (должен быть до @bot.message_handler)
bot = telebot.TeleBot(BOT_TOKEN)

# --- Настройка PostgreSQL ---
# Ищем ИМЕНА переменных, а не их ЗНАЧЕНИЯ
db_config = {
    'host': os.getenv('PG_HOST'),
    'database': os.getenv('PG_DATABASE'),
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASSWORD')
}

# --- 3. ИМПОРТ И ИНИЦИАЛИЗАЦИЯ ЛОГИКИ ---
# Импортируем агентов и MemoryManager после того, как все конфиги готовы
from agents import planner_agent, user_proxy
from memory_manager import MemoryManager

# Инициализация MemoryManager
try:
    memory = MemoryManager(db_config)
    print("✅ Подключение к PostgreSQL успешно.")
except Exception as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    exit()

# --- 4. ОБРАБОТЧИК СООБЩЕНИЙ ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_message = message.text
    bot.send_chat_action(chat_id, 'typing')

    try:
        # 1. Загрузка истории (8 пробелов отступа)
        history = memory.get_history(chat_id)

        # 2. Установка истории (8 пробелов)
        if history:
            planner_agent.chat_messages[user_proxy] = history

        # 3. Запуск диалога (8 пробелов)
        response = user_proxy.initiate_chat(
            planner_agent,
            message=user_message
        )

        # 4. Получение ответа (8 пробелов)
        final_reply = response.summary

        # 4.5. ПРОВЕРКА (ВАЖНО: Тоже 8 пробелов отступа, как и строки выше!)
        if not final_reply:
            final_reply = "Извините, агент не смог сформировать ответ."
            print("ВНИМАНИЕ: Агент Autogen вернул пустое сообщение.")

        # 5. Сохранение истории (8 пробелов)
        new_history = planner_agent.chat_messages[user_proxy]
        memory.update_history(chat_id, new_history)

        # 6. Отправка ответа (8 пробелов)
        bot.reply_to(message, final_reply)

    # except должен быть на одном уровне с try (4 пробела)
    except Exception as e:
        print(f"Ошибка в процессе обработки: {e}")
        bot.reply_to(message, "Произошла внутренняя ошибка при планировании. Проверьте логи.")


if __name__ == '__main__':
    print(f"🤖 Бот Smart Planner запущен, слушает {bot.get_me().username}...")
    # При запуске из WSL
    try:
        # Запускает бесконечный цикл обработки входящих сообщений Telegram
        bot.infinity_polling()
    except Exception as e:
        print(f"Критическая ошибка polling: {e}")
