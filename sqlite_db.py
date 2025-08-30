import sqlite3
import os
from datetime import datetime


def init_sqlite():
    """Инициализация SQLite базы данных"""
    try:
        conn = sqlite3.connect('applications.db', check_same_thread=False)
        cursor = conn.cursor()

        # Создаем таблицу если ее нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                experience TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        return conn
    except Exception as e:
        print(f"Ошибка создания базы данных: {e}")
        return None


def add_application_sqlite(user_id, username, full_name, phone, experience):
    """Добавление новой заявки в базу"""
    try:
        conn = init_sqlite()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO applications (user_id, username, full_name, phone, experience)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, full_name, phone, experience))
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        print(f"Ошибка добавления заявки: {e}")
    return False


def get_applications_from_db():
    """Получение всех заявок из базы"""
    try:
        conn = init_sqlite()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM applications ORDER BY created_at DESC')
            applications = cursor.fetchall()
            conn.close()
            return applications
    except Exception as e:
        print(f"Ошибка получения заявок: {e}")
    return []


def get_new_applications_from_db():
    """Получение только новых заявок"""
    try:
        conn = init_sqlite()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM applications WHERE status = "new" ORDER BY created_at DESC')
            applications = cursor.fetchall()
            conn.close()
            return applications
    except Exception as e:
        print(f"Ошибка получения новых заявок: {e}")
    return []


def send_db_to_admin(context, admin_id):
    """Отправка файла базы данных админу"""
    try:
        if os.path.exists('applications.db'):
            with open('applications.db', 'rb') as f:
                context.bot.send_document(
                    chat_id=admin_id,
                    document=f,
                    caption='📊 База данных с заявками\n\n'
                            'Для просмотра:\n'
                            '1. Скачайте файл\n'
                            '2. Откройте в DB Browser for SQLite\n'
                            '3. Перейдите во вкладку "Данные"\n'
                            '4. Выберите таблицу "applications"'
                )
            return True
    except Exception as e:
        print(f"Ошибка отправки файла: {e}")
    return False


# Инициализируем базу при импорте
init_sqlite()