"""
Скрипт миграции Felix Hub с версии 2.1 на 2.2

Что делает этот скрипт:
1. Создает таблицу mechanics
2. Добавляет поле mechanic_id в таблицу orders
3. Извлекает уникальных механиков из существующих заказов
4. Создает для них учетные записи
5. Связывает старые заказы с новыми механиками

ВАЖНО: Запускать только после резервного копирования БД!
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Mechanic, Order


def create_username_from_name(full_name):
    """Создать username из полного имени"""
    # Убираем пробелы, приводим к нижнему регистру
    username = full_name.strip().lower().replace(' ', '_')
    # Транслитерация русских букв (базовая)
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    username_translited = ''
    for char in username:
        username_translited += translit.get(char, char)
    
    # Удаляем недопустимые символы
    username_clean = ''.join(c for c in username_translited if c.isalnum() or c == '_')
    
    return username_clean or 'mechanic'


def generate_default_password():
    """Генерация дефолтного пароля"""
    return 'felix2025'


def migrate_to_v2_2():
    """Основная функция миграции"""
    print("🚀 Начало миграции Felix Hub v2.1 → v2.2")
    print("=" * 60)
    
    with app.app_context():
        # Шаг 1: Создание таблиц
        print("\n📋 Шаг 1: Создание новых таблиц...")
        try:
            db.create_all()
            
            # Добавляем колонку mechanic_id в таблицу orders (если ещё не добавлена)
            with db.engine.connect() as conn:
                # Проверяем, существует ли колонка
                result = conn.execute(db.text("PRAGMA table_info(orders)"))
                columns = [row[1] for row in result]
                
                if 'mechanic_id' not in columns:
                    print("   Добавление колонки mechanic_id в таблицу orders...")
                    conn.execute(db.text("ALTER TABLE orders ADD COLUMN mechanic_id INTEGER"))
                    conn.commit()
                    print("   ✓ Колонка mechanic_id добавлена")
                else:
                    print("   ✓ Колонка mechanic_id уже существует")
            
            print("✅ Таблицы созданы успешно")
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            return False
        
        # Шаг 2: Получение уникальных механиков
        print("\n👥 Шаг 2: Поиск уникальных механиков в заказах...")
        try:
            # Получаем все уникальные пары (имя, telegram_id)
            unique_mechanics = db.session.query(
                Order.mechanic_name,
                Order.telegram_id
            ).distinct().all()
            
            print(f"   Найдено уникальных механиков: {len(unique_mechanics)}")
            
            # Шаг 3: Создание учетных записей механиков
            print("\n🔐 Шаг 3: Создание учетных записей...")
            created_mechanics = {}
            default_password = generate_default_password()
            
            for mechanic_name, telegram_id in unique_mechanics:
                if not mechanic_name:
                    continue
                
                # Проверяем, не существует ли уже такой механик (по telegram_id или имени)
                existing = None
                if telegram_id:
                    existing = Mechanic.query.filter_by(telegram_id=telegram_id).first()
                
                if existing:
                    print(f"   ⚠️  Пропущен (уже существует): {mechanic_name}")
                    key = (mechanic_name, telegram_id)
                    created_mechanics[key] = existing.id
                    continue
                
                # Создаем username из имени
                username = create_username_from_name(mechanic_name)
                
                # Если username занят, добавляем цифру
                base_username = username
                counter = 1
                while Mechanic.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Создаем механика
                mechanic = Mechanic(
                    username=username,
                    password_hash=generate_password_hash(default_password),
                    full_name=mechanic_name,
                    telegram_id=telegram_id if telegram_id else None,
                    is_active=True,
                    notify_on_ready=True,
                    notify_on_processing=False,
                    language='ru'
                )
                
                db.session.add(mechanic)
                db.session.flush()  # Получить ID без коммита
                
                # Сохраняем соответствие имени и ID
                key = (mechanic_name, telegram_id)
                created_mechanics[key] = mechanic.id
                
                print(f"   ✓ Создан: {mechanic_name} → username: {username}")
            
            db.session.commit()
            print(f"✅ Создано механиков: {len(created_mechanics)}")
            
            # Шаг 4: Связывание заказов с механиками
            print("\n🔗 Шаг 4: Связывание заказов с механиками...")
            orders = Order.query.all()
            updated_count = 0
            
            for order in orders:
                key = (order.mechanic_name, order.telegram_id)
                if key in created_mechanics:
                    order.mechanic_id = created_mechanics[key]
                    updated_count += 1
            
            db.session.commit()
            print(f"✅ Обновлено заказов: {updated_count}")
            
            # Шаг 5: Статистика
            print("\n📊 Итоговая статистика:")
            print("=" * 60)
            total_mechanics = Mechanic.query.count()
            total_orders = Order.query.count()
            linked_orders = Order.query.filter(Order.mechanic_id.isnot(None)).count()
            
            print(f"   Всего механиков: {total_mechanics}")
            print(f"   Всего заказов: {total_orders}")
            print(f"   Связанных заказов: {linked_orders}")
            print(f"   Несвязанных заказов: {total_orders - linked_orders}")
            
            # Вывод информации о механиках
            print("\n👥 Созданные механики:")
            print("-" * 60)
            mechanics = Mechanic.query.all()
            for m in mechanics:
                orders_count = Order.query.filter_by(mechanic_id=m.id).count()
                print(f"   • {m.full_name:20} | username: {m.username:15} | заказов: {orders_count}")
            
            print("\n" + "=" * 60)
            print("✅ Миграция успешно завершена!")
            print("\n💡 ВАЖНАЯ ИНФОРМАЦИЯ:")
            print(f"   • Пароль по умолчанию для всех механиков: {default_password}")
            print("   • Механики могут войти на /mechanic/login")
            print("   • Рекомендуется сменить пароли при первом входе")
            print("   • Администратор может управлять механиками в /admin")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
            return False


def rollback_migration():
    """Откат миграции (удаление таблицы mechanics и связей)"""
    print("⚠️  ВНИМАНИЕ: Откат миграции!")
    print("Это удалит таблицу mechanics и связи с заказами")
    
    response = input("Вы уверены? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Откат отменен")
        return
    
    with app.app_context():
        try:
            # Удаляем связи в заказах
            db.session.execute("UPDATE orders SET mechanic_id = NULL")
            
            # Удаляем таблицу mechanics
            Mechanic.__table__.drop(db.engine)
            
            db.session.commit()
            print("✅ Откат выполнен")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка отката: {e}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Felix Hub - Миграция v2.1 → v2.2")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback_migration()
    else:
        print("\n⚠️  ПЕРЕД МИГРАЦИЕЙ:")
        print("   1. Убедитесь, что создана резервная копия БД")
        print("   2. Закройте все запущенные экземпляры приложения")
        print("   3. Прочитайте ROADMAP_v2.2.md")
        print("\n")
        
        response = input("Продолжить миграцию? (yes/no): ")
        if response.lower() == 'yes':
            success = migrate_to_v2_2()
            sys.exit(0 if success else 1)
        else:
            print("❌ Миграция отменена")
            sys.exit(1)
