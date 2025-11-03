"""
Миграция: Добавление таблицы категорий (categories) и заполнение
Версия: 2.2.2
Дата: 03.11.2024
"""

import os
import sys

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Category
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Дефолтные категории
DEFAULT_CATEGORIES = [
    'Тормоза',
    'Двигатель',
    'Подвеска',
    'Электрика',
    'Расходники'
]


def migrate():
    """Запуск миграции"""
    with app.app_context():
        try:
            print("🚀 Начало миграции: добавление таблицы категорий")
            
            # Создание таблицы categories
            print("📋 Создание таблицы categories...")
            db.create_all()
            print("✅ Таблица categories создана")
            
            # Проверка, есть ли уже категории в базе
            existing_count = Category.query.count()
            if existing_count > 0:
                print(f"ℹ️  В базе уже есть {existing_count} категорий, пропускаем импорт")
                return
            
            # Импорт дефолтных категорий
            print("📁 Импорт дефолтных категорий...")
            
            for idx, cat_name in enumerate(DEFAULT_CATEGORIES):
                category = Category(
                    name=cat_name,
                    is_active=True,
                    sort_order=idx * 10
                )
                db.session.add(category)
                print(f"  ✓ {cat_name}")
            
            db.session.commit()
            print(f"✅ Импортировано {len(DEFAULT_CATEGORIES)} категорий")
            
            # Вывод статистики
            print("\n📊 Статистика:")
            total = Category.query.count()
            active = Category.query.filter_by(is_active=True).count()
            print(f"  Всего категорий: {total}")
            print(f"  Активных: {active}")
            
            print("\n✅ Миграция успешно завершена!")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    migrate()
