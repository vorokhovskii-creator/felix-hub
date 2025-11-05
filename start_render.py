#!/usr/bin/env python3
"""
Безопасная обёртка для запуска приложения на Render
"""

import os
import sys
import shutil


def start_gunicorn():
    """Запуск Gunicorn с правильными параметрами"""
    port = os.getenv('PORT', '8000')

    # Диагностика окружения
    print("=" * 60)
    print("Felix Hub start diagnostics:")
    print(f" CWD: {os.getcwd()}")
    print(f" PYTHON: {sys.executable}")
    print(f" PATH: {os.getenv('PATH')}")
    print(f" PORT: {port}")
    print("=" * 60)

    # Проверим доступность gunicorn
    gunicorn_path = shutil.which('gunicorn')
    print(f" gunicorn found at: {gunicorn_path}")

    # Формируем команду запуска через python -m gunicorn (надежнее в venv)
    cmd = [
        sys.executable, '-m', 'gunicorn',
        'app:app',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--threads', '2',
        '--timeout', '120',
        '--log-level', 'info',
        '--access-logfile', '-',
        '--error-logfile', '-',
    ]

    print(f"🚀 Launching: {' '.join(cmd)}")
    print("=" * 60)

    # Передаем управление процессу gunicorn
    os.execv(sys.executable, cmd)


if __name__ == '__main__':
    start_gunicorn()
