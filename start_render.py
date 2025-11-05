#!/usr/bin/env python3
"""
Безопасная обёртка для запуска приложения на Render
"""

import os
import sys

def start_gunicorn():
    """Запуск Gunicorn с правильными параметрами"""
    port = os.getenv('PORT', '8000')
    
    cmd = [
        'gunicorn',
        'app:app',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--threads', '2',
        '--timeout', '120',
        '--log-level', 'info',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--preload'  # Загружаем приложение перед fork (инициализирует БД)
    ]
    
    print("="*60)
    print(f"🚀 Запуск Felix Hub на порту {port}")
    print(f"Команда: {' '.join(cmd)}")
    print("="*60)
    
    # Запускаем Gunicorn, передавая управление
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    start_gunicorn()
