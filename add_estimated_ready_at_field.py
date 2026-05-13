"""
Миграция: Добавление поля estimated_ready_at в таблицу orders

Это поле хранит расчетное время готовности заказа на основе очереди.
Запускается автоматически при старте приложения или вручную.

Использование:
    python add_estimated_ready_at_field.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine.url import make_url

# Загрузка переменных окружения
load_dotenv()

def run_migration():
    """Добавить поле estimated_ready_at в таблицу orders"""

    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/felix_hub.db')

    # Очистка и нормализация URL
    database_url = database_url.strip()
    if (database_url.startswith('"') and database_url.endswith('"')) or \
       (database_url.startswith("'") and database_url.endswith("'")):
        database_url = database_url[1:-1]

    # Исправление протокола для SQLAlchemy
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

    # Настройки подключения
    connect_args = {}
    if 'postgresql' in database_url:
        # Для продакшена (Railway, Render) требуется SSL
        # Для локальной разработки SSL не требуется
        if 'localhost' in database_url or '127.0.0.1' in database_url:
            connect_args = {"sslmode": "disable"}
        else:
            connect_args = {"sslmode": "require"}

    engine = create_engine(database_url, connect_args=connect_args)

    try:
        with engine.connect() as conn:
            # Проверяем, существует ли уже поле
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('orders')]

            if 'estimated_ready_at' in columns:
                print("✅ Поле estimated_ready_at уже существует в таблице orders")
                return

            # Добавляем новое поле
            if 'sqlite' in database_url:
                # SQLite синтаксис
                conn.execute(text("""
                    ALTER TABLE orders
                    ADD COLUMN estimated_ready_at DATETIME
                """))
            else:
                # PostgreSQL синтаксис
                conn.execute(text("""
                    ALTER TABLE orders
                    ADD COLUMN estimated_ready_at TIMESTAMP
                """))

            conn.commit()
            print("✅ Поле estimated_ready_at успешно добавлено в таблицу orders")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == '__main__':
    print("🔄 Запуск миграции: добавление поля estimated_ready_at...")
    run_migration()
    print("✅ Миграция завершена!")
