# agents.py
import calendar_tools # <-- Корректный импорт модуля
import autogen
import os
from dotenv import load_dotenv

load_dotenv()

# Убедитесь, что GROQ_API_KEY существует
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("ОШИБКА: GROQ_API_KEY не найден в файле .env или он пуст!")

# 1. Конфигурация LLM
config_list = [{
    "model": "llama-3.1-8b-instant",
    "api_key": os.getenv("GROQ_API_KEY"),
    "base_url": "https://api.groq.com/openai/v1",
    "timeout": 120,      # Увеличиваем ожидание до 120 секунд
    "max_retries": 5
}]

# 2. Агент Планировщик (Planner Agent)
planner_agent = autogen.AssistantAgent(
    name="Planner",
    llm_config={
        "config_list": config_list,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "create_calendar_event",
                    "description": "Создает событие в Google Календаре. Принимает summary и start_datetime в ISO 8601.",
                    # ИСПРАВЛЕНО: Используем schema из импортированного модуля calendar_tools
                    "parameters": calendar_tools.create_calendar_event.schema 
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
    
    # ИСПРАВЛЕНО: Ссылка на функцию через модуль calendar_tools
    function_map={"create_calendar_event": calendar_tools.create_calendar_event},
    
    llm_config={"config_list": config_list},
    # Максимальное количество автоответов должно быть больше 0, 
    # чтобы дать агентам шанс завершить задачу после вызова функции.
    # Установите 3 или 5. Если 0, диалог завершится слишком быстро.
    max_consecutive_auto_reply=1, 
)
