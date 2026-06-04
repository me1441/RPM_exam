#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчик заказов - Flask Backend
Сборка в exe: pyinstaller --onefile --windowed --add-data "templates;templates" --add-data "static;static" app.py
"""

import os
import sys
import json
import uuid
import webbrowser
import threading
import time
from datetime import datetime

# Определяем пути для PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from flask import Flask, render_template, request, jsonify, send_from_directory

# ==================== КОНФИГУРАЦИЯ ====================
app = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['SECRET_KEY'] = 'order-handler-secret-key-2026'
app.config['JSON_AS_ASCII'] = False

# Файл для хранения заказов
ORDERS_FILE = os.path.join(os.path.expanduser('~'), 'orders_data.json')

# ==================== ДАННЫЕ ТОВАРОВ ====================
PRODUCTS = {
    "1": {"id": 1, "name": "Ноутбук", "price": 45000, "stock": 10, "emoji": "💻",
          "images": [
              "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Процессор", "value": "Intel Core i5-1135G7"},
              {"label": "Оперативная память", "value": "16 GB DDR4"},
              {"label": "Накопитель", "value": "512 GB SSD"},
              {"label": "Экран", "value": '15.6" Full HD IPS'},
              {"label": "Видеокарта", "value": "Intel Iris Xe Graphics"},
              {"label": "Операционная система", "value": "Windows 11 Home"},
              {"label": "Вес", "value": "1.8 кг"},
              {"label": "Аккумулятор", "value": "До 8 часов работы"}
          ]},
    "2": {"id": 2, "name": "Телефон", "price": 35000, "stock": 15, "emoji": "📱",
          "images": [
              "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Процессор", "value": "Snapdragon 888"},
              {"label": "Оперативная память", "value": "8 GB"},
              {"label": "Накопитель", "value": "256 GB"},
              {"label": "Экран", "value": '6.5" AMOLED 120Hz'},
              {"label": "Камера", "value": "108 МП + 12 МП + 5 МП"},
              {"label": "Аккумулятор", "value": "5000 мАч"},
              {"label": "Быстрая зарядка", "value": "65W"},
              {"label": "Защита", "value": "IP68"}
          ]},
    "3": {"id": 3, "name": "Телевизор", "price": 55000, "stock": 5, "emoji": "📺",
          "images": [
              "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1461151304267-38535e780c79?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1613665813446-82a78c468a1d?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Диагональ", "value": '55" (139 см)'},
              {"label": "Разрешение", "value": "4K Ultra HD (3840x2160)"},
              {"label": "Технология", "value": "QLED"},
              {"label": "Частота обновления", "value": "120 Hz"},
              {"label": "Smart TV", "value": "Android TV 11"},
              {"label": "HDR", "value": "HDR10+, Dolby Vision"},
              {"label": "Звук", "value": "Dolby Atmos, 40W"},
              {"label": "Порты", "value": "4xHDMI 2.1, 3xUSB"}
          ]},
    "4": {"id": 4, "name": "Компьютер", "price": 75000, "stock": 50, "emoji": "🖥️",
          "images": [
              "https://images.unsplash.com/photo-1587831990711-23ca6441447b?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Процессор", "value": "AMD Ryzen 7 5800X"},
              {"label": "Оперативная память", "value": "32 GB DDR4 3200MHz"},
              {"label": "Видеокарта", "value": "NVIDIA RTX 3060 12GB"},
              {"label": "Накопитель", "value": "1 TB NVMe SSD"},
              {"label": "Блок питания", "value": "650W 80+ Gold"},
              {"label": "Корпус", "value": "Mid-Tower с RGB подсветкой"},
              {"label": "Охлаждение", "value": "Жидкостное СВО 240mm"},
              {"label": "Операционная система", "value": "Windows 11 Pro"}
          ]},
    "5": {"id": 5, "name": "Наушники", "price": 12000, "stock": 30, "emoji": "🎧",
          "images": [
              "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Тип", "value": "Беспроводные накладные"},
              {"label": "Драйверы", "value": "40 мм"},
              {"label": "Частотный диапазон", "value": "20 Гц – 20 кГц"},
              {"label": "Bluetooth", "value": "5.2"},
              {"label": "Активное шумоподавление", "value": "ANC"},
              {"label": "Время работы", "value": "До 35 часов"},
              {"label": "Зарядка", "value": "USB-C, быстрая зарядка"},
              {"label": "Вес", "value": "250 г"}
          ]},
    "6": {"id": 6, "name": "Умные часы", "price": 18000, "stock": 20, "emoji": "⌚",
          "images": [
              "https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Экран", "value": '1.75" AMOLED 390x450'},
              {"label": "Процессор", "value": "Dual-core 1.2 ГГц"},
              {"label": "Датчики", "value": "Пульс, SpO2, ECG, температура"},
              {"label": "GPS", "value": "GPS, ГЛОНАСС, Galileo"},
              {"label": "Защита", "value": "5ATM + IP68"},
              {"label": "Аккумулятор", "value": "450 мАч, до 14 дней"},
              {"label": "Материал корпуса", "value": "Алюминий"},
              {"label": "Совместимость", "value": "iOS 12+ / Android 8+"}
          ]},
    "7": {"id": 7, "name": "Планшет", "price": 32000, "stock": 12, "emoji": "📟",
          "images": [
              "https://images.unsplash.com/photo-1589739900243-4b52cd9b104e?q=80&w=704&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
              "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Экран", "value": '11" IPS LCD 2560x1600'},
              {"label": "Процессор", "value": "MediaTek Dimensity 9000"},
              {"label": "Оперативная память", "value": "8 GB LPDDR5"},
              {"label": "Накопитель", "value": "256 GB UFS 3.1"},
              {"label": "Аккумулятор", "value": "8600 мАч"},
              {"label": "Камеры", "value": "13 МП + 8 МП фронтальная"},
              {"label": "Операционная система", "value": "Android 14"},
              {"label": "Вес", "value": "480 г"}
          ]},
    "8": {"id": 8, "name": "Фотоаппарат", "price": 85000, "stock": 8, "emoji": "📷",
          "images": [
              "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600&h=400&fit=crop",
              "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&h=400&fit=crop"
          ],
          "specs": [
              {"label": "Матрица", "value": "APS-C 24.2 МП"},
              {"label": "Процессор изображения", "value": "DIGIC X"},
              {"label": "Видео", "value": "4K 60fps, Full HD 120fps"},
              {"label": "Автофокус", "value": "Dual Pixel CMOS AF II"},
              {"label": "ISO", "value": "100–51200 (расширенный до 204800)"},
              {"label": "Серийная съёмка", "value": "15 кадр/с механический, 23 кадр/с электронный"},
              {"label": "Экран", "value": '3" сенсорный поворотный'},
              {"label": "Вес", "value": "612 г (только корпус)"}
          ]}
}

# ==================== УТИЛИТЫ ====================
def load_orders():
    """Загрузка заказов из файла"""
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_orders(orders):
    """Сохранение заказов в файл"""
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def generate_order_id():
    """Генерация уникального ID заказа"""
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"

# ==================== API ROUTES ====================
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    """Получение списка товаров"""
    return jsonify({
        "success": True,
        "products": PRODUCTS,
        "count": len(PRODUCTS)
    })

@app.route('/api/products/<product_id>')
def get_product(product_id):
    """Получение информации о товаре"""
    product = PRODUCTS.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Товар не найден"}), 404
    return jsonify({"success": True, "product": product})

@app.route('/api/order', methods=['POST'])
def create_order():
    """Создание нового заказа"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400

        # Валидация
        required_fields = ['customer', 'products', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Отсутствует поле: {field}"}), 400

        customer = data['customer']
        if not all(k in customer for k in ['name', 'email', 'phone']):
            return jsonify({"success": False, "error": "Неполные данные клиента"}), 400

        # Создание заказа
        order = {
            "order_id": data.get('order_id', generate_order_id()),
            "date": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            "customer": customer,
            "products": data['products'],
            "total_amount": data.get('total_amount', 0),
            "payment_method": data['payment_method'],
            "comment": data.get('comment', ''),
            "status": "completed"
        }

        # Сохранение
        orders = load_orders()
        orders.insert(0, order)
        save_orders(orders)

        return jsonify({
            "success": True,
            "order": order,
            "message": "Заказ успешно создан"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders')
def get_orders():
    """Получение истории заказов"""
    orders = load_orders()
    return jsonify({
        "success": True,
        "orders": orders,
        "count": len(orders)
    })

@app.route('/api/stats')
def get_stats():
    """Статистика"""
    orders = load_orders()
    total_revenue = sum(o['total_amount'] for o in orders)
    return jsonify({
        "success": True,
        "total_orders": len(orders),
        "total_revenue": total_revenue,
        "products_count": len(PRODUCTS)
    })

# ==================== СТАТИЧЕСКИЕ ФАЙЛЫ ====================
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)

# ==================== ЗАПУСК ====================
def open_browser():
    """Открытие браузера после запуска сервера"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Создаём файл заказов если нет
    if not os.path.exists(ORDERS_FILE):
        save_orders([])

    # Открываем браузер в отдельном потоке
    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 50)
    print("🚀 Обработчик заказов запущен!")
    print("📍 URL: http://127.0.0.1:5000/")
    print("💾 Заказы сохраняются в:", ORDERS_FILE)
    print("=" * 50)

    # Запуск Flask
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
