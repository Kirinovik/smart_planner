# main.py
##
import telebot
import os
from dotenv import load_dotenv
import json
import calendar_tools
import traceback

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("КРИТИЧЕСКАЯ ОШИБКА: Токен Telegram не найден! Проверьте файл .env")
    exit()
import calendar_tools
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.delete_webhook()
    print("Старый Webhook успешно удален.")
except Exception as e:
    print(f"шибка при удалении Webhook (но это может быть нормально): {e}")

db_config = {
    'host': os.getenv('PG_HOST'),
    'database': os.getenv('PG_DATABASE'),
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASSWORD')
}


from agents import planner_agent, user_proxy
from memory_manager import MemoryManager

# Инициализация MemoryManager
try:
    memory = MemoryManager(db_config)
    print("Подключение к PostgreSQL успешно.")
except Exception as e:
    print(f"Ошибка подключения к PostgreSQL: {e}")
    exit()

user_proxy.register_for_execution(calendar_tools.create_calendar_event)
print("Функция create_calendar_event зарегистрирована для Autogen.")

# Обработка сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_message = message.text
    bot.send_chat_action(chat_id, 'typing')

    try:

        history = memory.get_history(chat_id)

        if history:
            planner_agent.chat_messages[user_proxy] = history

        #Запуск диалога
        response = user_proxy.initiate_chat(
            planner_agent,
            message=user_message
        )


        final_reply = response.summary


        if final_reply:
            new_history = planner_agent.chat_messages[user_proxy]
            memory.update_history(chat_id, new_history)
        else:
            final_reply = "Извините, агент не смог сформировать ответ."
            print("ВНИМАНИЕ: Агент Autogen вернул пустое сообщение.")

        # Отправка ответа
        bot.reply_to(message, final_reply)

    except Exception as e:
        error_message = f"КРИТИЧЕСКАЯ ОШИБКА ОБРАБОТКИ: {e}\n{traceback.format_exc()}"
        print(error_message)
        bot.reply_to(message, "Произошла внутренняя ошибка при планировании. Проверьте логи консоли.")



if __name__ == '__main__':
    print("ПРОВЕРКА GOOGLE АВТОРИЗАЦИИ")
    try:
        # Запуск авторизации (единоразово)
        calendar_tools.get_calendar_service()
        print("Google Calendar API доступен (файл token.json проверен).")
    except Exception as e:
        print(f"ОШИБКА АВТОРИЗАЦИИ GOOGLE: {e}")

        pass

    print(f"🤖 Бот Smart Planner запущен, слушает {bot.get_me().username}...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Критическая ошибка polling: {e}")
