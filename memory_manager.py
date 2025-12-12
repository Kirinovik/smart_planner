# memory_manager.py

import psycopg2
import json
from psycopg2 import extras

class MemoryManager:
    def __init__(self, db_config):
        # Инициализация подключения к PostgreSQL
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor(cursor_factory=extras.DictCursor)

    def get_history(self, chat_id: int) -> list:
        """Извлекает историю чата по ID."""
        self.cursor.execute("SELECT history FROM autogen_memory WHERE chat_id = %s", (chat_id,))
        result = self.cursor.fetchone()

        # История хранится как JSONB, нужно её декодировать
        return result['history'] if result and result['history'] else []

    def update_history(self, chat_id: int, history: list):
        """Сохраняет или обновляет историю чата."""
        history_json = json.dumps(history)
        self.cursor.execute("""
            INSERT INTO autogen_memory (chat_id, history)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) 
            DO UPDATE SET history = EXCLUDED.history;
        """, (chat_id, history_json))
        self.conn.commit()

    def close(self):
        """Закрывает соединение с базой данных."""
        self.conn.close()
