import os
from dotenv import load_dotenv

# 1. Загружаем переменные из файла .env в память компьютера
load_dotenv()

# 2. Собираем словарь параметров для базы данных, доставая их из памяти
DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}

# 3. Достаем настройки для Кафки
KAFKA_SERVER = os.getenv("KAFKA_SERVER")
TOPIC_NAME = os.getenv("KAFKA_TOPIC")