import os
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///felix_hub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создание папки для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Telegram настройки
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID')

# Модель данных
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    mechanic_name = db.Column(db.String(120), nullable=False)
    telegram_id = db.Column(db.String(50))
    category = db.Column(db.String(120), nullable=False)
    plate_number = db.Column(db.String(20), nullable=False)  # Гос номер вместо VIN
    selected_parts = db.Column(db.JSON)
    is_original = db.Column(db.Boolean, default=False)
    photo_url = db.Column(db.String(250))
    comment = db.Column(db.Text)
    status = db.Column(db.String(50), default='новый')
    printed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'mechanic_name': self.mechanic_name,
            'telegram_id': self.telegram_id,
            'category': self.category,
            'plate_number': self.plate_number,
            'selected_parts': self.selected_parts or [],
            'is_original': self.is_original,
            'photo_url': self.photo_url,
            'comment': self.comment,
            'status': self.status,
            'printed': self.printed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# Справочник категорий и запчастей
PARTS_CATALOG = {
    'Тормоза': ['Передние колодки', 'Задние колодки', 'Диски передние', 'Диски задние', 'Тормозная жидкость'],
    'Двигатель': ['Масло моторное', 'Масляный фильтр', 'Воздушный фильтр', 'Свечи зажигания', 'Ремень ГРМ'],
    'Подвеска': ['Амортизаторы передние', 'Амортизаторы задние', 'Пружины', 'Стойки стабилизатора', 'Рычаги'],
    'Электрика': ['Аккумулятор', 'Генератор', 'Стартер', 'Лампы', 'Датчики'],
    'Расходники': ['Антифриз', 'Омывайка', 'Салонный фильтр', 'Щётки стеклоочистителя', 'Технические жидкости']
}

# Функции для работы с Telegram
def send_telegram_message(chat_id, text):
    """Отправка сообщения в Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram bot token не настроен")
        return False
    
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def notify_admin_new_order(order):
    """Уведомление администратору о новом заказе"""
    if not TELEGRAM_ADMIN_CHAT_ID:
        return
    
    parts_list = '\n'.join([f"• {part}" for part in order.selected_parts])
    
    message = f"""🔔 <b>Новый заказ от {order.mechanic_name}</b>

📋 Заказ №{order.id}
🚗 Гос номер: <b>{order.plate_number}</b>
📦 Категория: {order.category}

<b>Детали:</b>
{parts_list}

{'🔧 Оригинал' if order.is_original else '💰 Аналог'}
⏰ {order.created_at.strftime('%d.%m.%Y %H:%M')}
"""
    
    if order.comment:
        message += f"\n💬 Комментарий: {order.comment}"
    
    send_telegram_message(TELEGRAM_ADMIN_CHAT_ID, message)

def notify_mechanic_order_ready(order):
    """Уведомление механику о готовности заказа"""
    if not order.telegram_id:
        return
    
    message = f"""✅ <b>Заказ №{order.id} готов!</b>

🚗 Авто: <b>{order.plate_number}</b>
📦 Категория: {order.category}

Забери детали у кладовщика 📦"""
    
    send_telegram_message(order.telegram_id, message)

def validate_plate_number(plate_number):
    """Валидация формата гос номера"""
    # Примеры допустимых форматов: 123-45-678, A123BC77, В456СТ199
    if not plate_number or len(plate_number) < 5:
        return False
    
    # Убираем пробелы и приводим к верхнему регистру
    plate_number = plate_number.strip().upper()
    
    # Базовая проверка: есть буквы или цифры
    if not re.search(r'[A-ZА-Я0-9]', plate_number):
        return False
    
    return True

def print_receipt(order):
    """Печать чека (симуляция - можно заменить на реальную печать)"""
    receipt = f"""
{'='*40}
СТО Felix
{'='*40}
Заказ №{order.id}
Механик: {order.mechanic_name}
Гос номер: {order.plate_number}
Категория: {order.category}
{'='*40}
Детали:
"""
    for part in order.selected_parts:
        receipt += f"- {part}\n"
    
    receipt += f"""{'='*40}
Статус: {order.status}
Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
{'='*40}
"""
    
    print(receipt)  # В продакшене здесь будет вызов принтера
    return receipt

# Маршруты приложения

@app.route('/')
def index():
    """Главная страница - выбор языка"""
    return render_template('index.html')

@app.route('/mechanic')
def mechanic():
    """Интерфейс механика"""
    lang = request.args.get('lang', 'ru')
    return render_template('mechanic.html', catalog=PARTS_CATALOG, lang=lang)

@app.route('/api/submit_order', methods=['POST'])
def submit_order():
    """API для создания нового заказа"""
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        if not data.get('mechanic_name'):
            return jsonify({'error': 'Имя механика обязательно'}), 400
        
        if not data.get('plate_number'):
            return jsonify({'error': 'Гос номер обязателен'}), 400
        
        if not validate_plate_number(data['plate_number']):
            return jsonify({'error': 'Неверный формат гос номера'}), 400
        
        if not data.get('category'):
            return jsonify({'error': 'Категория обязательна'}), 400
        
        if not data.get('selected_parts') or len(data['selected_parts']) == 0:
            return jsonify({'error': 'Выберите хотя бы одну деталь'}), 400
        
        # Создание нового заказа
        order = Order(
            mechanic_name=data['mechanic_name'],
            telegram_id=data.get('telegram_id'),
            category=data['category'],
            plate_number=data['plate_number'].strip().upper(),
            selected_parts=data['selected_parts'],
            is_original=data.get('is_original', False),
            photo_url=data.get('photo_url'),
            comment=data.get('comment'),
            status='новый'
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Отправка уведомления администратору
        notify_admin_new_order(order)
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Заказ успешно создан'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка создания заказа: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin():
    """Панель администратора"""
    # Простая авторизация (в продакшене использовать Flask-Login)
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Вход администратора"""
    if request.method == 'POST':
        # Простая проверка (в продакшене использовать хеши паролей)
        if request.form.get('password') == 'felix2025':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Неверный пароль')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Выход администратора"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/api/orders')
def get_orders():
    """API для получения списка заказов"""
    # Фильтрация
    status = request.args.get('status')
    plate_number = request.args.get('plate_number')
    mechanic = request.args.get('mechanic')
    
    query = Order.query
    
    if status and status != 'все':
        query = query.filter_by(status=status)
    
    if plate_number:
        query = query.filter(Order.plate_number.ilike(f'%{plate_number}%'))
    
    if mechanic:
        query = query.filter(Order.mechanic_name.ilike(f'%{mechanic}%'))
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """API для обновления заказа"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        old_status = order.status
        new_status = data.get('status')
        
        if new_status:
            order.status = new_status
        
        if 'printed' in data:
            order.printed = data['printed']
        
        db.session.commit()
        
        # Если статус изменён на "готово", отправить уведомление механику
        if old_status != 'готово' and new_status == 'готово':
            notify_mechanic_order_ready(order)
            
            # Автоматическая печать чека
            if not order.printed:
                print_receipt(order)
                order.printed = True
                db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/print', methods=['POST'])
def print_order(order_id):
    """API для печати чека"""
    try:
        order = Order.query.get_or_404(order_id)
        receipt = print_receipt(order)
        
        order.printed = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'receipt': receipt
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """API для удаления заказа"""
    try:
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Инициализация базы данных
def init_db():
    with app.app_context():
        db.create_all()
        print("✅ База данных инициализирована")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
