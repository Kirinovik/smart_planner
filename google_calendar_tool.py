# google_calendar_tool.py

from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# Инициализация сервиса Google Calendar
SERVICE_FILE = os.getenv("GOOGLE_CALENDAR_SERVICE_FILE")
SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_calendar_service():
    """Создает объект сервиса Google Calendar."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def create_calendar_event(summary: str, start_datetime: str) -> str:
    """
    Создает событие в Google Calendar.
    Аргументы:
    - summary (str): Заголовок события.
    - start_datetime (str): Дата и время в строгом ISO 8601 формате
                             (например, 2025-12-15T10:00:00+03:00).
    """
    try:
        service = create_calendar_service()

        # Логика Set/Code Node: Форматирование и добавление 1 часа
        start_dt = datetime.fromisoformat(start_datetime)
        end_dt = start_dt + timedelta(hours=1)

        event = {
            'summary': summary,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Moscow'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Moscow'},
        }

        service.events().insert(calendarId='primary', body=event).execute()

        return f"Событие '{summary}' успешно добавлено в Google Calendar на {start_dt.strftime('%d.%m.%Y в %H:%M')}, включая часовой пояс."

    except ValueError:
        # Если LLM передал неверный формат даты
        return "Ошибка: Неверный формат даты. Пожалуйста, убедитесь, что LLM использует ISO 8601 (например, YYYY-MM-DDT...)."
    except Exception as e:
        return f"Не удалось создать событие в календаре: {e}"
