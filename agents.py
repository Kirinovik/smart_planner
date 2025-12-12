# agents.py

import autogen
import os
from dotenv import load_dotenv
from google_calendar_tool import create_calendar_event

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("ОШИБКА: OPENAI_API_KEY не найден в файле .env или он пуст!")
# 1. Конфигурация LLM (ChatGPT)
config_list = [{
    "model": "gpt-5-mini",  # Рекомендуется для лучшего извлечения данных
    "api_key": api_key
}]

# 2. Агент Планировщик (Planner Agent)
# Аналог вашего AI Agent: принимает решение, когда вызывать функцию.
planner_agent = autogen.AssistantAgent(
    name="Planner",
    llm_config={"config_list": config_list},
    system_message=(
        "Ты - Умный Планировщик. Твоя задача — анализировать запросы пользователя. "
        "Если запрос касается планирования (создания) события, ты должен вызвать функцию "
        "'create_calendar_event'. Извлеки 'summary' и 'start_datetime' в строгом "
        "ISO 8601 формате, включая смещение часового пояса (например, 2025-12-15T10:00:00+03:00). "
        "Не отвечай текстом до тех пор, пока не получишь результат от инструмента."
    ),
)

# 3. Прокси-Агент Пользователя (User Proxy Agent)
# Аналог триггера Telegram и узла Set/Expression: получает сообщение,
# управляет вызовом функции и отправляет ответ пользователю.
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",  # Отключаем интерактивное взаимодействие в консоли
is_termination_msg=lambda x: "успешно добавлено" in x.get("content", "").lower()
                                 or "чем могу помочь?" not in x.get("content", "").lower(),
    code_execution_config={"use_docker": False},
    # Подключение функции
    function_map={"create_calendar_event": create_calendar_event},
)
