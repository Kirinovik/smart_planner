# main.py
##
import telebot
import os
from dotenv import load_dotenv
import json
import calendar_tools
import traceback

# --- 1. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
# Должна быть выполнена первой, чтобы os.getenv() работала
load_dotenv()

# --- 2. ИНИЦИАЛИЗАЦИЯ TELEGRAM И POSTGRES (ДО ИМПОРТА АГЕНТОВ/HANDLER) ---
# Получение токена Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Токен Telegram не найден! Проверьте файл .env")
    exit()
import calendar_tools
# Инициализация объекта 'bot' (должен быть до @bot.message_handler)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.delete_webhook()
    print("✅ Старый Webhook успешно удален.")
except Exception as e:
    # Игнорируем ошибку, если Webhook не был установлен (хотя это маловероятно)
    print(f"⚠️ Ошибка при удалении Webhook (но это может быть нормально): {e}")

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

user_proxy.register_for_execution(calendar_tools.create_calendar_event)
print("✅ Функция create_calendar_event зарегистрирована для Autogen.")

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
        if final_reply:
            new_history = planner_agent.chat_messages[user_proxy]
            memory.update_history(chat_id, new_history)
        else:
            final_reply = "Извините, агент не смог сформировать ответ."
            print("ВНИМАНИЕ: Агент Autogen вернул пустое сообщение.")

        # 6. Отправка ответа (8 пробелов)
        bot.reply_to(message, final_reply)

    except Exception as e:
        error_message = f"❌ КРИТИЧЕСКАЯ ОШИБКА ОБРАБОТКИ: {e}\n{traceback.format_exc()}"
        print(error_message)
        bot.reply_to(message, "Произошла внутренняя ошибка при планировании. Проверьте логи консоли.")

# --- 5. КОМАНДА ЗАПУСКА И АВТОРИЗАЦИЯ GOOGLE (НОВОЕ ИЗМЕНЕНИЕ) ---

if __name__ == '__main__':
    print("--- ⚙️ ПРОВЕРКА GOOGLE АВТОРИЗАЦИИ ---")
    try:
        # ЗАПУСК ПЕРВОЙ АВТОРИЗАЦИИ: Это откроет браузер при первом запуске!
        calendar_tools.get_calendar_service() 
        print("✅ Google Calendar API доступен (файл token.json проверен).")
    except Exception as e:
        print(f"❌ ОШИБКА АВТОРИЗАЦИИ GOOGLE: {e}")
        # Не выходим, чтобы дать боту шанс работать, если ошибка не критична, 
        # но лучше исправить ее перед началом работы.
        pass

    print(f"🤖 Бот Smart Planner запущен, слушает {bot.get_me().username}...")
    
    try:
        # Запускает бесконечный цикл обработки входящих сообщений Telegram
        # timeout=60 дает больше времени на ответ от сервера
        # long_polling_timeout=60 держит соединение открытым дольше
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Критическая ошибка polling: {e}")
