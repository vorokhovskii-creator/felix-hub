#!/usr/bin/env python3
"""
Скрипт инициализации базы данных на Render

Использование:
    python init_render_db.py
"""

import os
from app import app, db
from models import Mechanic

def init_database():
    """Инициализация базы данных с созданием таблиц"""
    with app.app_context():
        print("🔄 Инициализация базы данных...")
        
        # Создание всех таблиц
        db.create_all()
        print("✅ Таблицы созданы")
        
        # Проверка наличия механиков
        mechanic_count = Mechanic.query.count()
        print(f"📊 Найдено механиков: {mechanic_count}")
        
        if mechanic_count == 0:
            print("⚠️  База данных пуста. Создайте первого механика через админ-панель.")
            print("   URL: https://felix-hub.onrender.com/admin/login")
            print("   Пароль: felix2025")
        else:
            print(f"✅ База данных готова к работе ({mechanic_count} механиков)")

if __name__ == '__main__':
    init_database()
