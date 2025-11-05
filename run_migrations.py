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
                    # Validate table exists first
                    if table_name not in inspector.get_table_names():
                        print(f"⚠️  Таблица {table_name} не существует")
                        raise ValueError(f"Table {table_name} does not exist")
                    
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    return column_name in columns
                except ValueError:
                    # Re-raise validation errors
                    raise
                except Exception as e:
                    print(f"⚠️  Ошибка проверки колонки {table_name}.{column_name}: {e}")
                    # Re-raise to prevent silent failures
                    raise
            
            # Validate inputs to prevent SQL injection
            def validate_column_name(col_name):
                """Validate column name contains only safe characters"""
                import re
                if not re.match(r'^[a-z_][a-z0-9_]*$', col_name):
                    raise ValueError(f"Invalid column name: {col_name}")
                return col_name
            
            def validate_column_type(col_type):
                """Validate column type is in allowed list"""
                allowed_types = ['VARCHAR(250)', 'VARCHAR(120)', 'TEXT']
                if col_type not in allowed_types:
                    raise ValueError(f"Invalid column type: {col_type}")
                return col_type
            
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
                            # Validate inputs
                            col_name = validate_column_name(col_name)
                            col_type = validate_column_type(col_type)
                            
                            if not column_exists('parts', col_name):
                                print(f"  ➕ Добавление колонки '{col_name}' ({description})...")
                                # Use text() with validated inputs
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
                            # Validate inputs
                            col_name = validate_column_name(col_name)
                            col_type = validate_column_type(col_type)
                            
                            if not column_exists('categories', col_name):
                                print(f"  ➕ Добавление колонки '{col_name}' ({description})...")
                                # Use text() with validated inputs
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
