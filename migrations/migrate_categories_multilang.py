"""
Миграция: Добавление многоязычности для категорий (PostgreSQL-совместимая)
Версия: 2.2.5
Дата: 04.11.2024

Использование:
    python migrations/migrate_categories_multilang.py
"""

import os
import sys

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Category
from dotenv import load_dotenv
from sqlalchemy import text, inspect

# Загрузка переменных окружения
load_dotenv()

# Переводы категорий
CATEGORY_TRANSLATIONS = {
    'Тормоза': {
        'en': 'Brakes',
        'he': 'בלמים'
    },
    'Двигатель': {
        'en': 'Engine',
        'he': 'מנוע'
    },
    'Подвеска': {
        'en': 'Suspension',
        'he': 'מתלים'
    },
    'Электрика': {
        'en': 'Electrical',
        'he': 'חשמל'
    },
    'Расходники': {
        'en': 'Consumables',
        'he': 'מתכלים'
    },
    'Добавки': {
        'en': 'Additives',
        'he': 'תוספים'
    },
    'Типуль': {
        'en': 'Maintenance',
        'he': 'טיפול'
    }
}


def column_exists(conn, table_name, column_name):
    """Проверка существования колонки (PostgreSQL и SQLite)"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_translation_columns():
    """Добавляет колонки для переводов в таблицу categories"""
    print("📋 Добавление колонок для переводов...")
    
    try:
        # Проверяем, какие колонки уже существуют
        columns_to_add = []
        
        if not column_exists(db.engine, 'categories', 'name_en'):
            columns_to_add.append(('name_en', 'VARCHAR(120)'))
        
        if not column_exists(db.engine, 'categories', 'name_he'):
            columns_to_add.append(('name_he', 'VARCHAR(120)'))
        
        if not column_exists(db.engine, 'categories', 'name_ru'):
            columns_to_add.append(('name_ru', 'VARCHAR(120)'))
        
        if not columns_to_add:
            print("  ℹ️  Все колонки уже существуют")
            return True
        
        # Добавляем колонки
        with db.engine.connect() as conn:
            trans = conn.begin()
            try:
                for col_name, col_type in columns_to_add:
                    # PostgreSQL синтаксис
                    conn.execute(text(f"ALTER TABLE categories ADD COLUMN {col_name} {col_type}"))
                    print(f"  ✓ Добавлена колонка {col_name}")
                
                trans.commit()
                print("✅ Колонки успешно добавлены")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Ошибка добавления колонок: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Ошибка проверки колонок: {e}")
        return False


def update_category_translations():
    """Обновляет переводы для существующих категорий"""
    print("\n📁 Обновление переводов категорий...")
    updated = 0
    
    for ru_name, translations in CATEGORY_TRANSLATIONS.items():
        category = Category.query.filter_by(name=ru_name).first()
        
        if category:
            try:
                with db.engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        conn.execute(
                            text("""
                                UPDATE categories 
                                SET name_ru = :name_ru,
                                    name_en = :name_en,
                                    name_he = :name_he
                                WHERE id = :id
                            """),
                            {
                                'id': category.id,
                                'name_ru': ru_name,
                                'name_en': translations['en'],
                                'name_he': translations['he']
                            }
                        )
                        trans.commit()
                        
                        updated += 1
                        print(f"  ✓ {ru_name}")
                        print(f"    EN: {translations['en']}")
                        print(f"    HE: {translations['he']}")
                        
                    except Exception as e:
                        trans.rollback()
                        print(f"  ❌ Ошибка обновления {ru_name}: {e}")
                
            except Exception as e:
                print(f"  ❌ Ошибка соединения для {ru_name}: {e}")
        else:
            print(f"  ⚠️  Категория не найдена: {ru_name}")
    
    print(f"\n✅ Обновлено: {updated} категорий")
    return updated


def show_statistics():
    """Показывает статистику по категориям"""
    print("\n" + "="*60)
    print("📊 СТАТИСТИКА ПО КАТЕГОРИЯМ")
    print("="*60)
    
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    id,
                    name,
                    name_ru,
                    name_en,
                    name_he,
                    is_active
                FROM categories
                ORDER BY sort_order, name
            """))
            
            categories = result.fetchall()
            
            print(f"\nВсего категорий: {len(categories)}")
            print("\nДетали:")
            print("-" * 60)
            
            for cat in categories:
                print(f"\n#{cat[0]}: {cat[1]}")
                print(f"  RU: {cat[2] or 'не указано'}")
                print(f"  EN: {cat[3] or 'не указано'}")
                print(f"  HE: {cat[4] or 'не указано'}")
                print(f"  Активна: {'Да' if cat[5] else 'Нет'}")
    
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")


def migrate():
    """Запуск миграции"""
    with app.app_context():
        try:
            print("🚀 МИГРАЦИЯ: Добавление многоязычности для категорий")
            print("="*60)
            
            # Определяем тип БД
            db_url = db.engine.url
            db_type = 'PostgreSQL' if 'postgresql' in str(db_url) else 'SQLite'
            print(f"📊 База данных: {db_type}")
            print(f"📍 URL: {db_url}")
            print()
            
            # 1. Добавление колонок
            if not add_translation_columns():
                print("❌ Не удалось добавить колонки")
                return
            
            # 2. Обновление переводов
            update_category_translations()
            
            # 3. Статистика
            show_statistics()
            
            print("\n" + "="*60)
            print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    migrate()
