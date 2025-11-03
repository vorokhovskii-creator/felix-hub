"""
Модуль авторизации и аутентификации для Felix Hub v2.2

Предоставляет:
- Настройку Flask-Login
- Декораторы для защиты маршрутов
- Функции входа/выхода
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import LoginManager, current_user
from models import Mechanic

# Инициализация LoginManager
login_manager = LoginManager()
login_manager.login_view = 'mechanic_login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    """
    Загрузка пользователя по ID для Flask-Login
    """
    return Mechanic.query.get(int(user_id))


def admin_required(f):
    """
    Декоратор для защиты маршрутов администратора
    Проверяет наличие сессии администратора
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            # Для API запросов возвращаем JSON ошибку
            if request.is_json or request.path.startswith('/api/'):
                from flask import jsonify
                return jsonify({'error': 'Требуется авторизация администратора'}), 401
            # Для обычных запросов - редирект
            flash('Требуется авторизация администратора', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def mechanic_required(f):
    """
    Декоратор для защиты маршрутов механика
    Проверяет, что пользователь авторизован как механик и активен
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Для API запросов возвращаем JSON ошибку
            if request.is_json or request.path.startswith('/api/'):
                from flask import jsonify
                return jsonify({'error': 'Требуется авторизация механика'}), 401
            # Для обычных запросов - редирект
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('mechanic_login', next=request.url))
        
        if not current_user.is_active:
            # Для API запросов возвращаем JSON ошибку
            if request.is_json or request.path.startswith('/api/'):
                from flask import jsonify
                return jsonify({'error': 'Ваш аккаунт деактивирован'}), 403
            # Для обычных запросов - редирект
            flash('Ваш аккаунт деактивирован. Обратитесь к администратору', 'error')
            return redirect(url_for('mechanic_login'))
        
        return f(*args, **kwargs)
    return decorated_function


def check_mechanic_owns_order(order):
    """
    Проверка, принадлежит ли заказ текущему механику
    
    Args:
        order: объект Order
    
    Returns:
        bool: True если заказ принадлежит текущему механику
    """
    if not current_user.is_authenticated:
        return False
    
    return order.mechanic_id == current_user.id


def get_notification_settings(mechanic):
    """
    Получить настройки уведомлений механика
    
    Args:
        mechanic: объект Mechanic
    
    Returns:
        dict: словарь с настройками уведомлений
    """
    return {
        'notify_on_ready': mechanic.notify_on_ready,
        'notify_on_processing': mechanic.notify_on_processing,
        'notify_on_cancelled': mechanic.notify_on_cancelled
    }


def should_notify_mechanic(order, event_type):
    """
    Определить, нужно ли отправлять уведомление механику
    
    Args:
        order: объект Order
        event_type: тип события ('ready', 'processing', 'cancelled')
    
    Returns:
        bool: True если нужно отправить уведомление
    """
    if not order.mechanic:
        return False
    
    if not order.mechanic.telegram_id:
        return False
    
    settings = get_notification_settings(order.mechanic)
    
    if event_type == 'ready':
        return settings['notify_on_ready']
    elif event_type == 'processing':
        return settings['notify_on_processing']
    elif event_type == 'cancelled':
        return settings['notify_on_cancelled']
    
    return False
