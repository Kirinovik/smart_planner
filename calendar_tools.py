import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional

# Настройки
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
CALENDAR_ID = 'kirillnovikov1501@gmail.com'
TIME_ZONE = 'Europe/Moscow'

def get_calendar_service():
    """
    Авторизует пользователя через OAuth 2.0 и возвращает объект службы Google Calendar.
    """
    creds = None
    print("DEBUG: Функция get_calendar_service() запущена.")

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Обновление токена доступа...")
            creds.refresh(Request())
        else:
            print("Запуск первой авторизации...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except FileNotFoundError:
                raise FileNotFoundError(f"Файл {CREDENTIALS_FILE} не найден.")

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"Токен успешно сохранен в {TOKEN_FILE}.")

    return build('calendar', 'v3', credentials=creds)


def create_calendar_event(summary: str, start_datetime: str, end_datetime: Optional[str] = None) -> str:
    """
    Создает событие в Google Календаре.
    """
    try:
        service = get_calendar_service()

        if not end_datetime:
            try:
                start_dt_obj = datetime.datetime.fromisoformat(start_datetime)
                end_dt_obj = start_dt_obj + datetime.timedelta(hours=1)
                end_datetime = end_dt_obj.isoformat()
            except ValueError:
                end_datetime = start_datetime

        print(f"DEBUG [1]: Начинаем запрос к API. Summary: {summary}")

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_datetime,
                'timeZone': TIME_ZONE,
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': TIME_ZONE,
            },
        }

        # Запрос к API
        event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event
        ).execute()

        print(f"DEBUG [2]: Google вернул ответ. ID события: {event.get('id')}")
        print(f"DEBUG [3]: Полный URL события: {event.get('htmlLink')}")

        return f"Событие '{summary}' успешно добавлено в Google Календарь. URL: {event.get('htmlLink')}"

    except HttpError as e:
        error_msg = f"Ошибка API Google Calendar (HTTP {e.resp.status}): {e.content.decode()}"
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
        return f"Критическая ошибка Google Calendar: {e.resp.status}. Проверьте токен."

    except Exception as e:
        print(f"НЕИЗВЕСТНАЯ ОШИБКА: {e}")
        return f"Критическая ошибка Google Calendar: Проверьте консоль."


create_calendar_event.schema = {
    "name": "create_calendar_event",
    "description": "Создает событие в Google Календаре. Принимает название и время начала.",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Название события."
            },
            "start_datetime": {
                "type": "string",
                "description": "Время начала в ISO 8601 формате, включая часовой пояс (например, 2025-12-16T18:00:00+03:00)."
            },
            "end_datetime": {
                "type": "string",
                "description": "Время окончания в ISO 8601 формате (опционально)."
            }
        },
        "required": ["summary", "start_datetime"]
    }
}

def list_calendar_events(max_results=10):
    """Возвращает список ближайших событий из календаря."""
    service = get_calendar_service()
    # Получаем текущее время в формате ISO
    now = datetime.datetime.utcnow().isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return "На ближайшее время событий не найдено."

    result = "Ваши ближайшие события:\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))

        display_time = start.replace('T', ' ')[:16]
        result += f"- {display_time}: {event.get('summary', 'Без названия')}\n"

    return result

# Описание для Autogen
list_calendar_events.schema = {
    "parameters": {
        "type": "object",
        "properties": {
            "max_results": {
                "type": "integer",
                "description": "Количество событий для вывода (по умолчанию 10)."
            }
        }
    }
}


if __name__ == '__main__':
    test_start = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(microsecond=0).isoformat() + "+03:00"

    print("--- Запуск теста авторизации и создания события ---")

    result = create_calendar_event(
        summary="Тест прямого подключения Python",
        start_datetime=test_start,
        end_datetime=None
    )

    print("Результат вызова функции:")
    print(result)
