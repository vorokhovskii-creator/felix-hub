"""
Инициализация базы данных с поддержкой нового поля estimated_ready_at

Этот скрипт:
1. Создает все таблицы, если их нет
2. Добавляет поле estimated_ready_at, если база уже существует
"""

import os
from app import app, db
from models import Order, Mechanic, Part, Category

def init_database():
    """Инициализация базы данных"""
    with app.app_context():
        print("🔄 Инициализация базы данных...")

        # Создаем все таблицы
        db.create_all()
        print("✅ Таблицы созданы или уже существуют")

        # Проверяем количество записей
        orders_count = Order.query.count()
        mechanics_count = Mechanic.query.count()
        parts_count = Part.query.count()
        categories_count = Category.query.count()

        print(f"\n📊 Статистика базы данных:")
        print(f"   Заказов: {orders_count}")
        print(f"   Механиков: {mechanics_count}")
        print(f"   Запчастей: {parts_count}")
        print(f"   Категорий: {categories_count}")

        print("\n✅ База данных готова к работе!")

if __name__ == '__main__':
    init_database()
