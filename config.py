import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))  # Преобразуем в число