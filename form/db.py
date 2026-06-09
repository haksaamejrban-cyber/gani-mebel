import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv('/var/www/form/.env')

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True,
}

ca_path = os.getenv('MYSQL_CA_CERT_PATH')
if ca_path and os.path.isfile(ca_path):
    DB_CONFIG['ssl_ca'] = ca_path
else:
    # локальное подключение без SSL, если сертификат не найден
    DB_CONFIG['ssl_disabled'] = True


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def int_or_none(value):
    if value is None or value == '' or value == '10':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
