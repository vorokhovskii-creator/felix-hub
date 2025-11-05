#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Автоматические миграции при старте приложения
Выполняются автоматически при запуске на Render
"""

import os
from models import db, Category

def migrate_category_translations():
    """Миграция переводов категорий"""
    
    print("🔄 Проверка переводов категорий...")
    
    # Маппинг переводов для категорий
    translations = {
        'тормоза': {
            'name_ru': 'Тормоза',
            'name_en': 'Brakes',
            'name_he': 'בלמים'
        },
        'типуль': {
            'name_ru': 'Типуль',
            'name_en': 'Maintenance',
            'name_he': 'טיפול'
        },
        'жидкости\\масла': {
            'name_ru': 'Жидкости\\Масла',
            'name_en': 'Fluids\\Oils',
            'name_he': 'נוזלים\\שמנים'
        },
        'жидкост': {  # частичное совпадение
            'name_ru': 'Жидкости\\Масла',
            'name_en': 'Fluids\\Oils',
            'name_he': 'נוזלים\\שמנים'
        },
        'типуль\\кузов': {
            'name_ru': 'Типуль\\Кузов',
            'name_en': 'Maintenance\\Body',
            'name_he': 'טיפול\\מרכב'
        },
        'лампочк': {
            'name_ru': 'Лампочки',
            'name_en': 'Bulbs',
            'name_he': 'נורות'
        }
    }
    
    # Получаем все категории
    categories = Category.query.all()
    updated_count = 0
    
    for category in categories:
        # Нормализуем название для поиска
        cat_name_lower = category.name.lower()
        
        # Ищем подходящий перевод
        translation = None
        for key, trans in translations.items():
            if key in cat_name_lower:
                translation = trans
                break
        
        if translation:
            needs_update = False
            
            # Обновляем только если поля пустые или совпадают с name
            if not category.name_ru or category.name_ru == category.name:
                category.name_ru = translation['name_ru']
                needs_update = True
            
            if not category.name_en:
                category.name_en = translation['name_en']
                needs_update = True
            
            if not category.name_he:
                category.name_he = translation['name_he']
                needs_update = True
            
            if needs_update:
                print(f"✅ Обновлена: {category.name} → {category.name_he}")
                updated_count += 1
    
    # Сохраняем изменения
    if updated_count > 0:
        db.session.commit()
        print(f"✅ Обновлено категорий: {updated_count}")
    else:
        print("ℹ️  Все категории уже имеют переводы")
    
    return updated_count

def run_auto_migrations(app):
    """Запуск всех автоматических миграций"""
    with app.app_context():
        try:
            migrate_category_translations()
        except Exception as e:
            print(f"⚠️  Ошибка миграции: {e}")
            # Не останавливаем приложение из-за ошибки миграции
            pass
