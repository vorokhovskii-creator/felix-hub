/**
 * Модуль для работы с Desktop Notifications (уведомления на рабочий стол)
 * Поддерживает Web Notifications API
 */

class NotificationManager {
    constructor() {
        this.permission = 'default';
        this.checkPermission();
    }

    /**
     * Проверить текущее разрешение на уведомления
     */
    checkPermission() {
        if (!('Notification' in window)) {
            console.warn('Браузер не поддерживает уведомления');
            return false;
        }
        this.permission = Notification.permission;
        return this.permission === 'granted';
    }

    /**
     * Запросить разрешение на показ уведомлений
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('Браузер не поддерживает уведомления');
            return false;
        }

        if (this.permission === 'granted') {
            return true;
        }

        try {
            const permission = await Notification.requestPermission();
            this.permission = permission;
            return permission === 'granted';
        } catch (error) {
            console.error('Ошибка запроса разрешения на уведомления:', error);
            return false;
        }
    }

    /**
     * Показать уведомление
     * @param {string} title - Заголовок уведомления
     * @param {Object} options - Опции уведомления
     * @param {string} options.body - Текст уведомления
     * @param {string} options.icon - Иконка уведомления
     * @param {string} options.tag - Тег для группировки уведомлений
     * @param {boolean} options.requireInteraction - Требовать взаимодействия
     * @param {Function} options.onClick - Обработчик клика
     */
    async show(title, options = {}) {
        // Проверяем разрешение
        if (this.permission !== 'granted') {
            const granted = await this.requestPermission();
            if (!granted) {
                console.warn('Разрешение на уведомления не получено');
                return null;
            }
        }

        try {
            const notification = new Notification(title, {
                body: options.body || '',
                icon: options.icon || '/static/favicon.ico',
                tag: options.tag || 'felix-hub',
                requireInteraction: options.requireInteraction || false,
                badge: options.badge || '/static/favicon.ico',
                vibrate: options.vibrate || [200, 100, 200],
                silent: options.silent || false
            });

            // Обработчик клика
            if (options.onClick) {
                notification.onclick = (event) => {
                    event.preventDefault();
                    window.focus();
                    options.onClick(event);
                    notification.close();
                };
            } else {
                notification.onclick = (event) => {
                    event.preventDefault();
                    window.focus();
                    notification.close();
                };
            }

            // Автоматически закрыть через 10 секунд, если не требуется взаимодействие
            if (!options.requireInteraction) {
                setTimeout(() => notification.close(), 10000);
            }

            return notification;
        } catch (error) {
            console.error('Ошибка показа уведомления:', error);
            return null;
        }
    }

    /**
     * Показать уведомление о новом заказе (для админа)
     */
    async notifyNewOrder(orderId, mechanicName, plateNumber) {
        return this.show('🆕 Новый заказ!', {
            body: `Заказ №${orderId}\nМеханик: ${mechanicName}\nГос номер: ${plateNumber}`,
            tag: `new-order-${orderId}`,
            requireInteraction: true,
            onClick: () => {
                // Переход к заказу в админ-панели
                window.location.hash = `order-${orderId}`;
            }
        });
    }

    /**
     * Показать уведомление о готовности заказа (для механика)
     */
    async notifyOrderReady(orderId, plateNumber) {
        return this.show('✅ Заказ готов!', {
            body: `Заказ №${orderId}\nГос номер: ${plateNumber}\nМожете забирать запчасти`,
            tag: `ready-order-${orderId}`,
            requireInteraction: true,
            onClick: () => {
                // Переход к списку заказов
                if (window.location.pathname.includes('/mechanic')) {
                    window.location.href = '/mechanic/orders';
                } else {
                    window.location.href = '/orders';
                }
            }
        });
    }

    /**
     * Показать уведомление об изменении статуса
     */
    async notifyStatusChange(orderId, oldStatus, newStatus, plateNumber) {
        const statusEmoji = {
            'новый': '🆕',
            'в работе': '⚙️',
            'в ожидании запчасти': '⏳',
            'готово': '✅',
            'выдано': '📦',
            'отменено': '❌'
        };

        return this.show(`${statusEmoji[newStatus] || '📋'} Статус изменен`, {
            body: `Заказ №${orderId} (${plateNumber})\n${oldStatus} → ${newStatus}`,
            tag: `status-${orderId}`,
            requireInteraction: false
        });
    }
}

// Создаем глобальный экземпляр
window.notificationManager = new NotificationManager();
