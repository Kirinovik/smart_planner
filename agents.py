# agents.py
import calendar_tools
import autogen
import os
from dotenv import load_dotenv

load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("ОШИБКА:API_KEY не найден в файле .env или он пуст!")

# 1. Конфигурация LLM
config_list = [{
    "model": "gpt-5-mini",
    "api_key": os.getenv("OPENAI_API_KEY"),
#    "base_url": "https://api.groq.com/openai/v1",
    "timeout": 120,
    "max_retries": 5
}]

# 2. Агент Планировщик (Planner Agent)
planner_agent = autogen.AssistantAgent(
    name="Planner",
    llm_config={
        "config_list": config_list,
        "tools": [
            {
                "type": "function", # функция  добавления события
                "function": {
                    "name": "create_calendar_event",
                    "description": "Создает событие в Google Календаре. Принимает summary и start_datetime в ISO 8601.",
                    # ИСПРАВЛЕНО: Используем schema из импортированного модуля calendar_tools
                    "parameters": calendar_tools.create_calendar_event.schema["parameters"]
                }
            },
            {
                "type": "function", # функция вывода событий
                "function": {
                    "name": "list_calendar_events",
                    "description": "Получает список ближайших событий из календаря.",
                    "parameters": calendar_tools.list_calendar_events.schema["parameters"]
                }
             }

       ]
    },
    system_message=(
        "Ты - Умный Планировщик. Твоя задача — анализировать запросы пользователя. "
        "Если запрос касается планирования (создания) события, ты должен вызвать функцию "
        "'create_calendar_event'. Извлеки 'summary' и 'start_datetime' в строгом "
        "ISO 8601 формате, включая смещение часового пояса (например, 2025-12-15T10:00:00+03:00)."
        "КЛЮЧЕВОЕ ПРАВИЛО: Вызов должен быть в формате Python: "
        "create_calendar_event(summary='Название', start_datetime='ГГГГ-ММ-ДДTЧЧ:ММ:СС+03:00'). "
        "summary и start_datetime должны быть строками в кавычках. "
        "Не отвечай текстом до тех пор, пока не получишь результат от инструмента."
        "ТВОИ ВОЗМОЖНОСТИ:\n"
        "1. Создавать события: используй 'create_calendar_event'.\n"
        "2. Показывать список дел: если пользователь спрашивает 'что у меня запланировано', 'какие планы' или 'покажи календарь', "
        "используй функцию 'list_calendar_events'.\n\n"

        "После вывода списка событий или создания нового, всегда добавляй TERMINATE в конце."
   )
)

# 3. Прокси-Агент Пользователя (User Proxy Agent)
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: (
        "успешно добавлено" in (x.get("content") or "").lower()
        or (x.get("content") or "").rstrip().endswith("TERMINATE")
    ),
    code_execution_config={"use_docker": False},


    function_map={"create_calendar_event": calendar_tools.create_calendar_event,
                 "list_calendar_events": calendar_tools.list_calendar_events},

    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=1,
)
