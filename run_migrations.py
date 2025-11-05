#!/usr/bin/env python3
"""
Принудительная миграция базы данных для Render
Выполняется при каждом запуске приложения
"""

import os
from app import app, db
from sqlalchemy import inspect, text

def run_migrations():
    """Выполнить все необходимые миграции"""
    with app.app_context():
        try:
            print("="*60)
            print("🔄 ЗАПУСК МИГРАЦИЙ БАЗЫ ДАННЫХ")
            print("="*60)
            
            inspector = inspect(db.engine)
            
            # Проверка существования колонки
            def column_exists(table_name, column_name):
                try:
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    return column_name in columns
                except Exception as e:
                    print(f"⚠️  Ошибка проверки колонки {table_name}.{column_name}: {e}")
                    return False
            
            # Начинаем транзакцию
            with db.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # МИГРАЦИЯ 1: Таблица parts
                    if 'parts' in inspector.get_table_names():
                        print("\n📦 Миграция таблицы 'parts'...")
                        
                        migrations_parts = [
                            ("name_ru", "VARCHAR(250)", "Название на русском"),
                            ("name_en", "VARCHAR(250)", "Название на английском"),
                            ("name_he", "VARCHAR(250)", "Название на иврите"),
                            ("description_ru", "TEXT", "Описание на русском"),
                            ("description_en", "TEXT", "Описание на английском"),
                            ("description_he", "TEXT", "Описание на иврите"),
                        ]
                        
                        for col_name, col_type, description in migrations_parts:
                            if not column_exists('parts', col_name):
                                print(f"  ➕ Добавление колонки '{col_name}' ({description})...")
                                conn.execute(text(f"ALTER TABLE parts ADD COLUMN {col_name} {col_type}"))
                            else:
                                print(f"  ✓ Колонка '{col_name}' уже существует")
                        
                        print("  ✅ Таблица 'parts' обновлена!")
                    
                    # МИГРАЦИЯ 2: Таблица categories
                    if 'categories' in inspector.get_table_names():
                        print("\n📁 Миграция таблицы 'categories'...")
                        
                        migrations_categories = [
                            ("name_ru", "VARCHAR(120)", "Название на русском"),
                            ("name_en", "VARCHAR(120)", "Название на английском"),
                            ("name_he", "VARCHAR(120)", "Название на иврите"),
                        ]
                        
                        for col_name, col_type, description in migrations_categories:
                            if not column_exists('categories', col_name):
                                print(f"  ➕ Добавление колонки '{col_name}' ({description})...")
                                conn.execute(text(f"ALTER TABLE categories ADD COLUMN {col_name} {col_type}"))
                            else:
                                print(f"  ✓ Колонка '{col_name}' уже существует")
                        
                        print("  ✅ Таблица 'categories' обновлена!")
                    
                    # Коммитим все изменения
                    trans.commit()
                    
                    print("\n" + "="*60)
                    print("✅ ВСЕ МИГРАЦИИ УСПЕШНО ВЫПОЛНЕНЫ!")
                    print("="*60)
                    
                except Exception as e:
                    trans.rollback()
                    print(f"\n❌ ОШИБКА МИГРАЦИИ: {e}")
                    print("Откат изменений...")
                    raise
                    
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    run_migrations()
    print("\n🚀 Миграции завершены. Запуск приложения...")
