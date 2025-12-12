# /home/kirill/smart_planner_autogen/calendar_tools.py

import os
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# КРИТИЧЕСКИ ВАЖНО: Замените на URL вашего вебхука (n8n, Zapier и т.д.)
# Убедитесь, что эта переменная есть в вашем файле .env
CALENDAR_WEBHOOK_URL = os.getenv("CALENDAR_WEBHOOK_URL")

def create_calendar_event(summary: str, start_datetime: str, end_datetime: str = None) -> str:
    """
    Создает событие в календаре, отправляя данные на внешний вебхук.
    """
    logger.info("--- ФУНКЦИЯ CREATE_CALENDAR_EVENT ВЫЗВАНА ---")
    logger.info(f"Параметры: Summary={summary}, Start={start_datetime}")

    if not CALENDAR_WEBHOOK_URL:
        logger.error("CALENDAR_WEBHOOK_URL не настроен в .env!")
        return "Ошибка: Не настроен URL для внешнего API календаря."

    payload = {
        "summary": summary,
        "start": start_datetime,
        "end": end_datetime if end_datetime else start_datetime, # Простая логика: если нет конца, конец = начало
        "timezone": "Europe/Moscow" # или другой часовой пояс по умолчанию
    }

    logger.info(f"Отправка запроса на создание события: {summary}...")

    try:
        logger.info(f"Отправка POST-запроса на URL: {CALENDAR_WEBHOOK_URL}")
        response = requests.post(CALENDAR_WEBHOOK_URL, json=payload, timeout=10)
        logger.info(f"Ответ от API: Status={response.status_code}, Text={response.text}")
        response.raise_for_status() # Вызывает исключение для 4xx/5xx ошибок

        # Если API календаря возвращает успешный JSON ответ
        if response.status_code in [200, 201]:
            # Важно: В ответе должно быть ключевое слово "успешно добавлено"
            return f"Событие '{summary}' успешно добавлено в календарь через Webhook."
        else:
            return f"Ошибка API календаря: Статус {response.status_code}. Ответ: {response.text}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка HTTP-запроса к Webhook: {e}")
        return f"Критическая ошибка подключения: Не удалось отправить данные на Webhook. {e}"
    except Exception as e:
        logger.error(f"Неизвестная ошибка в функции: {e}")
        return f"Неизвестная ошибка: {e}"


