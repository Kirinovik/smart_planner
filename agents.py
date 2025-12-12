
# agents.py

import autogen
import os
from dotenv import load_dotenv
from google_calendar_tool import create_calendar_event
#from calendar_tools import create_calendar_event

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("ОШИБКА: OPENAI_API_KEY не найден в файле .env или он пуст!")
# 1. Конфигурация LLM (ChatGPT)
config_list = [{
    "model": "llama-3.1-8b-instant",  # Рекомендуется для лучшего извлечения данных
    "api_key": os.getenv("GROQ_API_KEY"),
    "base_url": "https://api.groq.com/openai/v1"
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
        "ISO 8601 формате, включая смещение часового пояса (например, 2025-12-15T10:00:00+03:00)."
        "КЛЮЧЕВОЕ ПРАВИЛО: Вызов должен быть в формате Python: "
        "create_calendar_event(summary='Название', start_datetime='ГГГГ-ММ-ДДTЧЧ:ММ:СС+03:00'). "
        "summary и start_datetime должны быть строками в кавычках."
        "Не отвечай текстом до тех пор, пока не получишь результат от инструмента."
        "Не отвечай текстом до тех пор, пока не получишь результат от инструмента."
    ),
)

# 3. Прокси-Агент Пользователя (User Proxy Agent)
# Аналог триггера Telegram и узла Set/Expression: получает сообщение,
# управляет вызовом функции и отправляет ответ пользователю.
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",  # Отключаем интерактивное взаимодействие в консоли
    is_termination_msg=lambda x: ( "успешно добавлено" in x.get("content", "").lower()
                             or x.get("content", "").rstrip().endswith("TERMINATE")
			     or ("?" not in x.get("content", "") and not x.get("function_call"))
),
    code_execution_config={
	"use_docker": False,
    },
    # Подключение функции
    function_map={"create_calendar_event": create_calendar_event},
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=0,
)
