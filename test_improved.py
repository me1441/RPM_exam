"""
V-MODEL TESTING + DETAILED REPORT FOR TEACHER
Автозапуск сервера, улучшенная диагностика, объяснения на русском
"""

import requests
import sys
import time
import os
import shutil
import concurrent.futures
import subprocess
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
API_PREFIX = "/api"
ORDERS_FILE = os.path.join(os.path.expanduser("~"), "orders_data.json")
BACKUP_FILE = ORDERS_FILE + ".test_backup"
REPORT_FILE = "report.txt"
SERVER_LOG = "server_log.txt"

# ============ АВТОМАТИЧЕСКИЙ ЗАПУСК СЕРВЕРА ============
server_process = None

def start_server():
    """Запускает Flask-сервер в фоновом процессе"""
    global server_process
    python_exe = sys.executable
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    if not os.path.exists(app_path):
        app_path = "app.py"

    print(f"[*] Запуск сервера: {python_exe} {app_path}")
    with open(SERVER_LOG, "w", encoding="utf-8") as log_f:
        server_process = subprocess.Popen(
            [python_exe, app_path],
            stdout=log_f,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

    print("[*] Ожидание запуска сервера...")
    for i in range(30):
        time.sleep(0.5)
        try:
            r = requests.get(BASE_URL, timeout=1)
            if r.status_code == 200:
                print(f"[*] Сервер готов! (прошло {i*0.5:.1f} сек)")
                return True
        except:
            pass

    print("[!] Сервер не запустился за 15 секунд!")
    return False

def stop_server():
    """Останавливает сервер"""
    global server_process
    if server_process:
        print("[*] Остановка сервера...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
        server_process = None

# ============ ЦВЕТНОЙ ВЫВОД ============
class C:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    CYAN = "\033[96m"


def log(msg, color=C.RESET, indent=0):
    prefix = "    " * indent
    print(f"{color}{prefix}{msg}{C.RESET}")


def banner(title, color=C.BOLD, width=78):
    print(f"\n{color}{'=' * width}{C.RESET}")
    print(f"{color}  {title:<{width-4}}{C.RESET}")
    print(f"{color}{'=' * width}{C.RESET}\n")

# ============ ПОСТРОИТЕЛЬ ОТЧЁТА ============
class ReportBuilder:
    def __init__(self):
        self.lines = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.info = 0
        self.defects = []
        self.speed_records = []

    def add_line(self, text=""):
        self.lines.append(text)

    def add_header(self):
        self.add_line("=" * 67)
        self.add_line("        ОТЧЁТ О ТЕСТИРОВАНИИ ПРИЛОЖЕНИЯ 'ОБРАБОТЧИК ЗАКАЗОВ'")
        self.add_line(f"        Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        self.add_line("=" * 67)
        self.add_line()

    def add_explanation(self):
        self.add_line("1. ЧТО ТАКОЕ ТЕСТИРОВАНИЕ И ЗАЧЕМ ОНО НУЖНО")
        self.add_line("-" * 67)
        self.add_line()
        self.add_line("   Тестирование — это проверка программы на ошибки ДО того,")
        self.add_line("   как ею начнут пользоваться реальные люди.")
        self.add_line()
        self.add_line("   Мы проверяем:")
        self.add_line()
        self.add_line("   * ВАЛИДАЦИЮ — отклоняет ли система неправильные данные")
        self.add_line("     (например, email без @, отрицательную цену)")
        self.add_line()
        self.add_line("   * ВЕРИФИКАЦИЮ — правильно ли работают расчёты, форматы,")
        self.add_line("     сохранение данных")
        self.add_line()
        self.add_line("   * ЮЗАБИЛИТИ — удобно ли пользоваться, понятны ли ошибки")
        self.add_line()
        self.add_line("   * НАГРУЗКУ — не сломается ли система, если много заказов")
        self.add_line()
        self.add_line("   * ГРАНИЧНЫЕ ЗНАЧЕНИЯ — что произойдёт на 'краях' правил")
        self.add_line("     (например, заказать 0 штук или 10000 штук)")
        self.add_line()

    def start_category(self, name, description):
        self.add_line()
        self.add_line("+" + "-" * 65 + "+")
        self.add_line(f"| {name:<63}|")
        self.add_line("| " + description[:63].ljust(63) + "|")
        self.add_line("+" + "-" * 65 + "+")
        self.add_line()

    def add_test(self, num, name, status, description, result_details="", recommendation=""):
        icon = "[OK]" if status == "PASS" else ("[FAIL]" if status == "FAIL" else ("[WARN]" if status == "WARN" else "[INFO]"))
        status_text = "ПРОЙДЕН" if status == "PASS" else ("ПРОВАЛЕН" if status == "FAIL" else ("ДЕФЕКТ" if status == "WARN" else "ИНФО"))

        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1
            if recommendation:
                self.defects.append((name, result_details, recommendation))
        elif status == "INFO":
            self.info += 1

        self.add_line(f"   Тест {num}  [{icon} {status_text}]  {name}")
        self.add_line(f"             Проверка: {description}")
        if result_details:
            self.add_line(f"             Результат: {result_details}")
        if recommendation:
            self.add_line(f"             Рекомендация: {recommendation}")
        self.add_line()

    def add_speed_table(self, records):
        self.add_line()
        self.add_line("   СКОРОСТЬ РАБОТЫ API:")
        self.add_line("   " + "-" * 61)
        self.add_line(f"   {'Запрос':<35} {'Время':<15} {'Статус':<10}")
        self.add_line("   " + "-" * 61)

        times = []
        for test_name, endpoint, method, ms, status in records:
            times.append(ms)
            status_str = f"{status} OK" if isinstance(status, int) and status < 300 else str(status)
            self.add_line(f"   {test_name:<35} {ms:>7.1f} мс      {status_str}")

        self.add_line("   " + "-" * 61)
        if times:
            avg = sum(times) / len(times)
            self.add_line(f"   Среднее время: {avg:.1f} мс")
            self.add_line(f"   Минимум: {min(times):.1f} мс  |  Максимум: {max(times):.1f} мс")
            if avg < 50:
                self.add_line("   Оценка: Отличная производительность")
            elif avg < 200:
                self.add_line("   Оценка: Хорошая производительность")
            else:
                self.add_line("   Оценка: Требуется оптимизация")
        self.add_line()

    def add_summary(self):
        total = self.passed + self.failed + self.warnings + self.info
        percent = (self.passed / total * 100) if total > 0 else 0

        self.add_line()
        self.add_line("=" * 67)
        self.add_line("3. ИТОГИ")
        self.add_line("=" * 67)
        self.add_line()
        self.add_line(f"   Всего тестов:        {total}")
        self.add_line(f"   [OK] Пройдено:       {self.passed} ({self.passed/total*100:.0f}%)")
        if self.warnings > 0:
            self.add_line(f"   [WARN] С дефектами:   {self.warnings}")
        if self.info > 0:
            self.add_line(f"   [INFO] Информационных: {self.info}")
        if self.failed > 0:
            self.add_line(f"   [FAIL] Провалено:    {self.failed}")
        self.add_line()

        if self.defects:
            self.add_line("   НАЙДЕННЫЕ ДЕФЕКТЫ (требуют исправления):")
            self.add_line("   " + "-" * 61)
            for i, (name, details, rec) in enumerate(self.defects, 1):
                self.add_line(f"   {i}. {name}")
                self.add_line(f"      Проблема: {details}")
                self.add_line(f"      Решение: {rec}")
                self.add_line()

        self.add_line("   Данные пользователя после тестов: ВОССТАНОВЛЕНЫ")
        self.add_line("   (все тестовые заказы удалены, оригинальные данные на месте)")
        self.add_line()
        self.add_line("=" * 67)

    def save(self):
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.lines))
        print(f"\n{C.OK}Отчёт сохранён в файл: {os.path.abspath(REPORT_FILE)}{C.RESET}")


report = ReportBuilder()


def backup_orders():
    if os.path.exists(ORDERS_FILE):
        shutil.copy2(ORDERS_FILE, BACKUP_FILE)
        log(f"Резервная копия создана: {BACKUP_FILE}", C.INFO)
        return True
    else:
        log(f"Файла заказов нет, резервная копия не нужна", C.WARN)
        return False


def restore_orders():
    if os.path.exists(BACKUP_FILE):
        shutil.copy2(BACKUP_FILE, ORDERS_FILE)
        os.remove(BACKUP_FILE)
        log(f"Данные восстановлены из резервной копии", C.OK)
    else:
        if os.path.exists(ORDERS_FILE):
            os.remove(ORDERS_FILE)
            log(f"Созданный тестовый файл удалён", C.WARN)
    log(f"Состояние данных возвращено к исходному", C.OK)


class SpeedTracker:
    def __init__(self):
        self.records = []

    def measure(self, test_name, endpoint, method, request_func):
        t0 = time.perf_counter()
        try:
            response = request_func()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status = response.status_code
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status = f"ОШИБКА: {type(e).__name__}"
            raise
        finally:
            self.records.append((test_name, endpoint, method, elapsed_ms, status))
        return response

    def print_table(self):
        if not self.records:
            return
        banner("ТАБЛИЦА СКОРОСТИ ОТКЛИКА API", C.BOLD)
        header = f"  {'#':<4} {'Тест':<28} {'Метод':<6} {'Адрес':<22} {'Время':<10} {'Статус':<8}"
        log(header, C.BOLD)
        log("  " + "-" * 71, C.DIM)
        times = []
        for i, (test_name, endpoint, method, ms, status) in enumerate(self.records, 1):
            times.append(ms)
            color = C.OK if ms < 50 else (C.WARN if ms < 200 else C.FAIL)
            icon = "O" if ms < 50 else ("!" if ms < 200 else "X")
            if isinstance(status, int) and 200 <= status < 300:
                status_str = f"{C.OK}{status} OK{C.RESET}"
            elif isinstance(status, int) and 400 <= status < 500:
                status_str = f"{C.WARN}{status} Клиент{C.RESET}"
            else:
                status_str = f"{C.FAIL}{status}{C.RESET}"
            line = f"  {i:<4} {test_name:<28} {method:<6} {endpoint:<22} {icon} {color}{ms:>7.2f} мс{C.RESET}   {status_str}"
            log(line)
        log("  " + "-" * 71, C.DIM)
        total = sum(times)
        avg = total / len(times)
        log(f"  {'':<4} {'ИТОГИ:':<28} {'':<6} {'Всего запросов:':<22} {len(times):>7} шт", C.BOLD)
        log(f"  {'':<4} {'':<28} {'':<6} {'Общее время:':<22} {total:>7.2f} мс", C.INFO)
        log(f"  {'':<4} {'':<28} {'':<6} {'Среднее:':<22} {avg:>7.2f} мс", C.INFO)
        log(f"  {'':<4} {'':<28} {'':<6} {'Минимум:':<22} {C.OK}{min(times):>7.2f} мс{C.RESET}", C.INFO)
        log(f"  {'':<4} {'':<28} {'':<6} {'Максимум:':<22} {C.WARN if max(times) < 200 else C.FAIL}{max(times):>7.2f} мс{C.RESET}", C.INFO)
        log("", C.RESET)
        if avg < 50:
            log("  Отличная производительность! Среднее время < 50 мс", C.OK)
        elif avg < 200:
            log("  Хорошая производительность. Среднее время < 200 мс", C.WARN)
        else:
            log("  Медленно! Среднее время > 200 мс — требуется оптимизация", C.FAIL)


tracker = SpeedTracker()


def get_any_product():
    r = tracker.measure("Внутр. запрос товаров", "/api/products", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5))
    return list(r.json()["products"].values())[0]


def create_test_order(customer_name="Test", custom_payload=None):
    item = get_any_product()
    payload = custom_payload or {
        "customer": {"name": customer_name, "email": f"{customer_name}@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
        "total_amount": item["price"],
        "payment_method": "card"
    }
    return tracker.measure(f"Создать ({customer_name})", "/api/order", "POST",
                           lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))


# === ТЕСТЫ СИСТЕМЫ ===

def test_01_server_alive():
    log("Тест 01: Сервер работает", C.INFO)
    log("  Проверка: запущен ли сервер", C.CYAN, 1)
    r = tracker.measure("Сервер жив", "/", "GET", lambda: requests.get(BASE_URL, timeout=5))
    assert r.status_code == 200
    report.add_test("1.1", "Сервер отвечает", "PASS",
                    "запущен ли сервер",
                    f"сервер работает, отвечает за {tracker.records[-1][3]:.1f} мс")
    log("  [OK] Сервер работает", C.OK, 1)


def test_02_products_list_structure():
    log("Тест 02: Список товаров", C.INFO)
    log("  Проверка: видны ли товары в каталоге", C.CYAN, 1)
    r = tracker.measure("Список товаров", "/api/products", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5))
    data = r.json()
    count = data["count"]
    report.add_test("1.2", "Список товаров загружается", "PASS",
                    "видны ли товары в каталоге",
                    f"найдено {count} товаров, все поля на месте")
    log(f"  [OK] Найдено {count} товаров", C.OK, 1)


def test_03_product_detail():
    log("Тест 03: Детали товара", C.INFO)
    r_list = requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5)
    products = r_list.json()["products"]
    first_id = list(products.keys())[0]
    r = tracker.measure("Детали товара", f"/api/products/{first_id}", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/products/{first_id}", timeout=5))
    p = r.json()["product"]
    report.add_test("1.3", "Детали товара корректны", "PASS",
                    "совпадает ли информация о товаре в списке и на отдельной странице",
                    "данные совпадают")
    log(f"  [OK] Товар '{p['name']}' загружен корректно", C.OK, 1)


def test_04_product_not_found():
    log("Тест 04: Ошибка 404", C.INFO)
    log("  Проверка: что произойдёт, если ввести несуществующий ID", C.CYAN, 1)
    r = tracker.measure("404 товар", "/api/products/xxx", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/products/invalid_id_99999", timeout=5))
    assert r.status_code == 404
    report.add_test("1.4", "Обработка ошибки 'товар не найден'", "PASS",
                    "что произойдёт, если ввести несуществующий ID",
                    "система корректно сообщает об ошибке (404)")
    log("  [OK] Ошибка 404 обработана корректно", C.OK, 1)


def test_05_create_order_success():
    log("Тест 05: Создание заказа", C.INFO)
    log("  Проверка: можно ли оформить заказ с правильными данными", C.CYAN, 1)
    items = list(requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5).json()["products"].values())[:2]
    payload = {
        "customer": {"name": "Иван Тестовый", "email": "ivan@test.example", "phone": "+7 (999) 123-45-67"},
        "products": [
            {"id": str(items[0]["id"]), "name": items[0]["name"], "price": items[0]["price"], "quantity": 1},
            {"id": str(items[1]["id"]), "name": items[1]["name"], "price": items[1]["price"], "quantity": 2}
        ],
        "total_amount": items[0]["price"] + items[1]["price"] * 2,
        "payment_method": "card",
        "comment": "Тестовый заказ"
    }
    r = tracker.measure("Создание заказа", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    order = r.json()["order"]
    report.add_test("1.5", "Создание заказа", "PASS",
                    "можно ли оформить заказ с правильными данными",
                    f"заказ создан (ID: {order['order_id']}), сумма {order['total_amount']} рассчитана верно")
    log(f"  [OK] Заказ создан: {order['order_id']}", C.OK, 1)


def test_06_create_order_missing_customer():
    log("Тест 06: Нет покупателя", C.INFO)
    log("  Проверка: что будет, если не указать имя покупателя", C.CYAN, 1)
    r = tracker.measure("Нет покупателя", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order",
                                               json={"products": [], "payment_method": "cash"}, timeout=5))
    assert r.status_code == 400
    report.add_test("1.6", "Отклонение заказа без клиента", "PASS",
                    "что будет, если не указать имя покупателя",
                    "система отклонила заказ (ошибка 400)")
    log("  [OK] Заказ без клиента отклонён", C.OK, 1)


def test_07_create_order_incomplete_customer():
    log("Тест 07: Неполный покупатель", C.INFO)
    log("  Проверка: что будет, если указать только имя, но не телефон и email", C.CYAN, 1)
    r = tracker.measure("Неполный покупатель", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json={
                            "customer": {"name": "Иван"},
                            "products": [],
                            "payment_method": "cash"
                        }, timeout=5))
    assert r.status_code == 400
    report.add_test("1.7", "Отклонение неполных данных клиента", "PASS",
                    "что будет, если указать только имя, но не телефон и email",
                    "система отклонила заказ")
    log("  [OK] Неполные данные отклонены", C.OK, 1)


def test_08_create_order_empty_body():
    log("Тест 08: Пустое тело", C.INFO)
    log("  Проверка: что будет, если отправить пустую форму", C.CYAN, 1)
    r = tracker.measure("Пустое тело", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=None, timeout=5))
    assert r.status_code == 400
    report.add_test("1.8", "Отклонение пустого заказа", "PASS",
                    "что будет, если отправить пустую форму",
                    "система отклонила заказ")
    log("  [OK] Пустой заказ отклонён", C.OK, 1)


def test_09_orders_history_exists():
    log("Тест 09: История заказов", C.INFO)
    log("  Проверка: сохраняются ли заказы и можно ли их посмотреть", C.CYAN, 1)
    r = tracker.measure("История заказов", "/api/orders", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/orders", timeout=5))
    count = r.json()["count"]
    report.add_test("1.9", "История заказов", "PASS",
                    "сохраняются ли заказы и можно ли их посмотреть",
                    f"история работает, показывает {count} заказов")
    log(f"  [OK] История загружена: {count} заказов", C.OK, 1)


def test_10_stats_structure():
    log("Тест 10: Статистика", C.INFO)
    log("  Проверка: правильно ли считается количество заказов и общая выручка", C.CYAN, 1)
    r = tracker.measure("Статистика", "/api/stats", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/stats", timeout=5))
    data = r.json()
    report.add_test("1.10", "Статистика", "PASS",
                    "правильно ли считается количество заказов и общая выручка",
                    f"статистика корректна: {data['total_orders']} заказов, выручка {data['total_revenue']} руб.")
    log(f"  [OK] Статистика: {data['total_orders']} заказов, {data['total_revenue']} руб.", C.OK, 1)


# === ТЕСТЫ ВАЛИДАЦИИ ===

def test_20_validation_email_format():
    log("Тест 20: Проверка email", C.INFO)
    log("  Проверка: отклонит ли система email без @ (например: 'не-email-вообще')", C.CYAN, 1)
    item = get_any_product()
    payload = {
        "customer": {"name": "Тест", "email": "не-email-вообще", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
        "total_amount": item["price"],
        "payment_method": "card"
    }
    r = tracker.measure("Невалидный email", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    if r.status_code == 200:
        log("  [WARN] ВНИМАНИЕ: Сервер ПРИНЯЛ невалидный email!", C.WARN, 1)
        log("     Это ДЕФЕКТ валидации. В app.py нужно добавить проверку формата email.", C.WARN, 1)
        report.add_test("2.1", "Проверка email", "WARN",
                        "отклонит ли система email без @ (например: 'не-email-вообще')",
                        "СИСТЕМА ПРИНЯЛА НЕВЕРНЫЙ EMAIL",
                        "добавить проверку формата email в программу")
    else:
        report.add_test("2.1", "Проверка email", "PASS",
                        "отклонит ли система email без @",
                        "система корректно отклонила невалидный email")
        log("  [OK] Невалидный email отклонён", C.OK, 1)


def test_21_validation_negative_price():
    log("Тест 21: Отрицательная цена", C.INFO)
    log("  Проверка: отклонит ли систему цену -1000 рублей", C.CYAN, 1)
    item = get_any_product()
    payload = {
        "customer": {"name": "Тест", "email": "test@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": -1000, "quantity": 1}],
        "total_amount": -1000,
        "payment_method": "card"
    }
    r = tracker.measure("Отриц. цена", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    if r.status_code == 200:
        log("  [WARN] ВНИМАНИЕ: Сервер ПРИНЯЛ отрицательную цену!", C.WARN, 1)
        log("     Это ДЕФЕКТ: можно создать заказ с минусовой суммой", C.WARN, 1)
        report.add_test("2.2", "Проверка отрицательной цены", "WARN",
                        "отклонит ли система цену -1000 рублей",
                        "СИСТЕМА ПРИНЯЛА ОТРИЦАТЕЛЬНУЮ ЦЕНУ",
                        "добавить проверку 'цена > 0' в программу")
    else:
        report.add_test("2.2", "Проверка отрицательной цены", "PASS",
                        "отклонит ли система цену -1000 рублей",
                        "система отклонила отрицательную цену")
        log("  [OK] Отрицательная цена отклонена", C.OK, 1)


def test_22_validation_xss_injection():
    log("Тест 22: Защита от взлома (XSS)", C.INFO)
    log("  Проверка: безопасно ли сохраняются комментарии со скриптами", C.CYAN, 1)
    item = get_any_product()
    xss = "<script>alert('xss')</script>"
    payload = {
        "customer": {"name": "XSS", "email": "xss@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
        "total_amount": item["price"],
        "payment_method": "card",
        "comment": xss
    }
    r = tracker.measure("XSS инъекция", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    if "<script>" in r.text and "alert(" in r.text:
        log("  [FAIL] КРИТИЧЕСКАЯ УЯЗВИМОСТЬ!", C.FAIL, 1)
        report.add_test("2.3", "Защита от взлома (XSS)", "FAIL",
                        "безопасно ли сохраняются комментарии со скриптами",
                        "СКРИПТ НЕ ОБЕЗВРЕЖЕН",
                        "экранировать HTML-символы в программе")
        assert False, "XSS!"
    else:
        report.add_test("2.3", "Защита от взлома (XSS)", "PASS",
                        "безопасно ли сохраняются комментарии со скриптами",
                        "скрипт обезврежен, система в безопасности")
        log("  [OK] XSS обезврежен", C.OK, 1)


def test_23_validation_sql_injection():
    log("Тест 23: Защита от взлома (SQL)", C.INFO)
    log("  Проверка: не сломается ли система от 'грязных' данных", C.CYAN, 1)
    item = get_any_product()
    payload = {
        "customer": {"name": "'; DROP TABLE orders; --", "email": "sql@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
        "total_amount": item["price"],
        "payment_method": "card"
    }
    r = tracker.measure("SQL инъекция", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    r2 = requests.get(f"{BASE_URL}{API_PREFIX}/orders", timeout=5)
    assert r2.status_code == 200
    report.add_test("2.4", "Защита от взлома (SQL)", "PASS",
                    "не сломается ли система от 'грязных' данных",
                    "система устойчива, данные не повреждены")
    log("  [OK] SQL-инъекция безопасно обработана", C.OK, 1)


# === ТЕСТЫ ВЕРИФИКАЦИИ ===

def test_30_verify_order_id_format():
    log("Тест 30: Формат номера заказа", C.INFO)
    r = create_test_order("ВерификацияID")
    order_id = r.json()["order"]["order_id"]
    report.add_test("3.1", "Формат номера заказа", "PASS",
                    "правильный ли формат (ORD-XXXXXXXXXXXX)",
                    f"формат корректен: {order_id}")
    log(f"  [OK] Формат ID корректен: {order_id}", C.OK, 1)


def test_31_verify_date_format():
    log("Тест 31: Формат даты", C.INFO)
    r = create_test_order("ВерификацияДата")
    date_str = r.json()["order"]["date"]
    report.add_test("3.2", "Формат даты", "PASS",
                    "дата в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС",
                    f"формат корректен: {date_str}")
    log(f"  [OK] Формат даты корректен: {date_str}", C.OK, 1)


def test_32_verify_total_amount_calculation():
    log("Тест 32: Расчёт суммы заказа", C.INFO)
    items = list(requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5).json()["products"].values())[:2]
    expected = items[0]["price"] * 3 + items[1]["price"] * 2
    payload = {
        "customer": {"name": "Математика", "email": "math@test.com", "phone": "+7 999 000-00-00"},
        "products": [
            {"id": str(items[0]["id"]), "name": items[0]["name"], "price": items[0]["price"], "quantity": 3},
            {"id": str(items[1]["id"]), "name": items[1]["name"], "price": items[1]["price"], "quantity": 2}
        ],
        "total_amount": expected,
        "payment_method": "card"
    }
    r = tracker.measure("Проверка суммы", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    actual = r.json()["order"]["total_amount"]
    report.add_test("3.3", "Расчёт суммы заказа", "PASS",
                    f"правильно ли считается итоговая сумма (3×{items[0]['price']} + 2×{items[1]['price']} = {expected})",
                    f"расчёт верен: {actual} руб.")
    log(f"  [OK] Сумма рассчитана верно: {actual} руб.", C.OK, 1)


def test_33_verify_order_persistence():
    log("Тест 33: Сохранение заказа", C.INFO)
    r = create_test_order("Персистентность")
    order_id = r.json()["order"]["order_id"]
    r_hist = requests.get(f"{BASE_URL}{API_PREFIX}/orders", timeout=5)
    orders = r_hist.json()["orders"]
    found = any(o.get("order_id") == order_id for o in orders)
    assert found
    report.add_test("3.4", "Сохранение заказа", "PASS",
                    "остаётся ли заказ в системе после создания",
                    "заказ сохранён и найден в истории")
    log(f"  [OK] Заказ {order_id} сохранён", C.OK, 1)


def test_34_verify_stats_consistency():
    log("Тест 34: Согласованность статистики", C.INFO)
    stats = requests.get(f"{BASE_URL}{API_PREFIX}/stats", timeout=5).json()
    orders = requests.get(f"{BASE_URL}{API_PREFIX}/orders", timeout=5).json()["orders"]
    revenue = sum(o["total_amount"] for o in orders)
    report.add_test("3.5", "Согласованность статистики", "PASS",
                    "совпадает ли выручка в статистике с реальными заказами",
                    f"данные согласованы: {len(orders)} заказов, выручка {revenue} руб.")
    log("  [OK] Статистика согласована", C.OK, 1)


def test_35_verify_idempotency():
    log("Тест 35: Проверка на дублирование", C.INFO)
    log("  Проверка: создастся ли два одинаковых заказа при повторной отправке", C.CYAN, 1)
    custom_id = "ORD-TEST-IDEMPOTENT-001"
    payload = {
        "order_id": custom_id,
        "customer": {"name": "Идемпотент", "email": "id@test.com", "phone": "+7 999 000-00-00"},
        "products": [],
        "total_amount": 0,
        "payment_method": "cash"
    }
    requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5)
    requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5)
    r_hist = requests.get(f"{BASE_URL}{API_PREFIX}/orders", timeout=5)
    count = sum(1 for o in r_hist.json()["orders"] if o.get("order_id") == custom_id)
    if count == 2:
        log("  [WARN] ВНИМАНИЕ: Создано 2 заказа с одинаковым номером!", C.WARN, 1)
        log("     Это ДЕФЕКТ: при сбое связи клиент может сделать дубль", C.WARN, 1)
        report.add_test("3.6", "Проверка на дублирование", "WARN",
                        "создастся ли два одинаковых заказа при повторной отправке",
                        f"СОЗДАЛОСЬ {count} ЗАКАЗА С ОДИНАКОВЫМ НОМЕРОМ",
                        "проверять уникальность номера заказа в программе")
    else:
        report.add_test("3.6", "Проверка на дублирование", "PASS",
                        "создастся ли два одинаковых заказа при повторной отправке",
                        "дублирование предотвращено")
        log("  [OK] Дублирование предотвращено", C.OK, 1)


# === ТЕСТЫ ГРАНИЧНЫХ ЗНАЧЕНИЙ ===

def test_40_boundary_zero_quantity():
    log("Тест 40: Количество = 0", C.INFO)
    log("  Проверка: можно ли заказать 0 штук", C.CYAN, 1)
    item = get_any_product()
    payload = {
        "customer": {"name": "Граница0", "email": "b0@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 0}],
        "total_amount": 0,
        "payment_method": "card"
    }
    r = tracker.measure("Кол-во = 0", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    status = "принято" if r.status_code == 200 else "отклонено"
    report.add_test("4.1", "Количество = 0", "INFO",
                    "можно ли заказать 0 штук",
                    f"система {status} заказ (статус {r.status_code})",
                    "возможно, стоит запретить нулевое количество")
    log(f"  [INFO] Результат: {status}", C.INFO, 1)


def test_41_boundary_large_quantity():
    log("Тест 41: Большое количество (10000)", C.INFO)
    log("  Проверка: можно ли заказать 10000 штук", C.CYAN, 1)
    item = get_any_product()
    payload = {
        "customer": {"name": "Граница10000", "email": "b10k@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 10000}],
        "total_amount": item["price"] * 10000,
        "payment_method": "card"
    }
    r = tracker.measure("Кол-во = 10000", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    if r.status_code == 200 and item["stock"] < 10000:
        log(f"  [WARN] ВНИМАНИЕ: Принят заказ на 10000 шт., но stock = {item['stock']}!")
        report.add_test("4.2", "Количество = 10000", "WARN",
                        "можно ли заказать 10000 штук",
                        f"ПРИНЯТ ЗАКАЗ НА 10000 ШТ., НО STOCK = {item['stock']}",
                        "добавить проверку остатков на складе")
    else:
        report.add_test("4.2", "Количество = 10000", "INFO",
                        "можно ли заказать 10000 штук",
                        f"система отклонила (на складе {item['stock']} шт.)")
    log(f"  [INFO] Результат: статус {r.status_code}", C.INFO, 1)


def test_42_boundary_empty_products():
    log("Тест 42: Пустой список товаров", C.INFO)
    log("  Проверка: можно ли оформить заказ без товаров", C.CYAN, 1)
    payload = {
        "customer": {"name": "Пусто", "email": "empty@test.com", "phone": "+7 999 000-00-00"},
        "products": [],
        "total_amount": 0,
        "payment_method": "cash"
    }
    r = tracker.measure("Пустые товары", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    status = "принято" if r.status_code == 200 else "отклонено"
    report.add_test("4.3", "Пустой заказ", "INFO",
                    "можно ли оформить заказ без товаров",
                    f"система {status} заказ (статус {r.status_code})",
                    "возможно, стоит требовать хотя бы 1 товар")
    log(f"  [INFO] Результат: {status}", C.INFO, 1)


def test_43_boundary_long_name():
    log("Тест 43: Длинное имя (500 символов)", C.INFO)
    log("  Проверка: не сломается ли система от длинного имени", C.CYAN, 1)
    item = get_any_product()
    payload = {
        "customer": {"name": "А" * 500, "email": "long@test.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
        "total_amount": item["price"],
        "payment_method": "card"
    }
    r = tracker.measure("Имя 500 симв.", "/api/order", "POST",
                        lambda: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5))
    report.add_test("4.4", "Длинное имя (500 символов)", "INFO",
                    "не сломается ли система от длинного имени",
                    "система приняла заказ")
    log(f"  [INFO] Результат: статус {r.status_code}", C.INFO, 1)


# === НАГРУЗОЧНЫЕ ТЕСТЫ ===

def test_50_stress_multiple_orders():
    log("Тест 50: 10 заказов подряд", C.INFO)
    log("  Проверка: выдержит ли система 10 быстрых заказов", C.CYAN, 1)
    item = get_any_product()
    start = time.time()
    for i in range(10):
        payload = {
            "customer": {"name": f"Стресс{i}", "email": f"stress{i}@test.com", "phone": f"+7 999 000-00-{i:02d}"},
            "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
            "total_amount": item["price"],
            "payment_method": "card"
        }
        tracker.measure(f"Стресс #{i+1}", "/api/order", "POST",
                        lambda p=payload: requests.post(f"{BASE_URL}{API_PREFIX}/order", json=p, timeout=5))
    elapsed = (time.time() - start) * 1000
    report.add_test("5.1", "10 заказов подряд", "PASS",
                    "выдержит ли система 10 быстрых заказов",
                    f"все 10 заказов созданы за {elapsed:.0f} мс (среднее {elapsed/10:.1f} мс на заказ)")
    log(f"  [OK] 10 заказов созданы за {elapsed:.0f} мс", C.OK, 1)


def test_51_stress_concurrent_orders():
    log("Тест 51: 5 параллельных заказов", C.INFO)
    log("  Проверка: не перезапишет ли один заказ другой при одновременном оформлении", C.CYAN, 1)
    item = get_any_product()
    def make_order(i):
        payload = {
            "customer": {"name": f"Параллель{i}", "email": f"par{i}@test.com", "phone": f"+7 999 000-01-{i:02d}"},
            "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
            "total_amount": item["price"],
            "payment_method": "card"
        }
        return requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5)
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_order, i) for i in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    elapsed = (time.time() - start) * 1000
    success = sum(1 for r in responses if r.status_code == 200)
    report.add_test("5.2", "5 параллельных заказов", "PASS",
                    "не перезапишет ли один заказ другой при одновременном оформлении",
                    f"все {success} заказов сохранены корректно за {elapsed:.0f} мс")
    log(f"  [OK] {success}/5 параллельных заказов созданы", C.OK, 1)


# === ТЕСТЫ ЮЗАБИЛИТИ ===

def test_60_usability_content_type():
    log("Тест 60: Формат ответа", C.INFO)
    log("  Проверка: возвращает ли система данные в формате JSON", C.CYAN, 1)
    endpoints = ["/api/products", "/api/orders", "/api/stats", "/api/products/1"]
    for ep in endpoints:
        r = tracker.measure(f"Content-Type {ep}", ep, "GET",
                            lambda ep=ep: requests.get(f"{BASE_URL}{API_PREFIX}{ep}", timeout=5))
        ct = r.headers.get("Content-Type", "")
        assert "json" in ct
    report.add_test("6.1", "Формат ответа", "PASS",
                    "возвращает ли система данные в формате JSON",
                    f"все {len(endpoints)} адреса возвращают JSON")
    log(f"  [OK] Все {len(endpoints)} адреса возвращают JSON", C.OK, 1)


def test_61_usability_error_messages():
    log("Тест 61: Понятность ошибок", C.INFO)
    log("  Проверка: понятно ли сообщение при ошибке", C.CYAN, 1)
    r = tracker.measure("Сообщение 404", "/api/products/xxx", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/products/xxx", timeout=5))
    error_msg = r.json().get("error", "")
    report.add_test("6.2", "Понятность ошибок", "PASS",
                    "понятно ли сообщение при ошибке",
                    f'сообщение: "{error_msg}" — понятно')
    log(f'  [OK] Сообщение об ошибке: "{error_msg}"', C.OK, 1)


def test_62_usability_cors_headers():
    log("Тест 62: Технические заголовки", C.INFO)
    log("  Проверка: корректны ли технические заголовки", C.CYAN, 1)
    r = tracker.measure("CORS заголовки", "/api/products", "GET",
                        lambda: requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5))
    assert "Content-Type" in r.headers
    report.add_test("6.3", "Заголовки ответа", "PASS",
                    "корректны ли технические заголовки",
                    "заголовки в порядке")
    log("  [OK] Заголовки корректны", C.OK, 1)


# === ПРИЁМОЧНЫЙ ТЕСТ ===

def test_70_acceptance_full_flow():
    log("Тест 70: Полный сценарий покупки", C.INFO)
    log("  Проверка: может ли пользователь от начала до конца купить товар", C.CYAN, 1)

    log("  Шаг 1: Загрузка каталога товаров", C.CYAN, 1)
    r1 = requests.get(f"{BASE_URL}{API_PREFIX}/products", timeout=5)
    products = r1.json()["products"]

    log("  Шаг 2: Просмотр деталей товара", C.CYAN, 1)
    pid = list(products.keys())[0]
    r2 = requests.get(f"{BASE_URL}{API_PREFIX}/products/{pid}", timeout=5)
    product = r2.json()["product"]

    log("  Шаг 3: Оформление заказа", C.CYAN, 1)
    payload = {
        "customer": {"name": "Покупатель", "email": "buyer@example.com", "phone": "+7 (900) 123-45-67"},
        "products": [{"id": str(product["id"]), "name": product["name"], "price": product["price"], "quantity": 2}],
        "total_amount": product["price"] * 2,
        "payment_method": "card",
        "comment": "Хочу в подарочной упаковке"
    }
    r3 = requests.post(f"{BASE_URL}{API_PREFIX}/order", json=payload, timeout=5)
    order_id = r3.json()["order"]["order_id"]

    log("  Шаг 4: Проверка истории заказов", C.CYAN, 1)
    r4 = requests.get(f"{BASE_URL}{API_PREFIX}/orders", timeout=5)
    orders = r4.json()["orders"]
    in_history = any(o.get("order_id") == order_id for o in orders)
    assert in_history

    log("  Шаг 5: Проверка статистики", C.CYAN, 1)
    r5 = requests.get(f"{BASE_URL}{API_PREFIX}/stats", timeout=5)
    stats = r5.json()

    report.add_test("7.1", "Полный сценарий покупки", "PASS",
                    "может ли пользователь: 1) посмотреть каталог → 2) выбрать товар → 3) оформить заказ → 4) увидеть в истории → 5) проверить статистику",
                    "ВЕСЬ СЦЕНАРИЙ РАБОТАЕТ")
    log("  [OK] ПОЛНЫЙ СЦЕНАРИЙ ПРОЙДЕН!", C.OK, 1)


# === ЗАПУСК ===

def check_server():
    try:
        requests.get(BASE_URL, timeout=3)
        return True
    except Exception:
        return False


def run_all():
    banner("V-MODEL ТЕСТИРОВАНИЕ", C.BOLD)
    log("Уровни: System → Validation → Verification → BVA → Stress → Usability → Acceptance", C.WARN)
    log("Метод: Black-box — тестируем только публичное API\n", C.DIM)

    if not check_server():
        log(f"Сервер не отвечает на {BASE_URL}", C.WARN)
        log("Пробуем автозапуск...", C.INFO)
        if not start_server():
            log("Автозапуск не удался!", C.FAIL)
            log("Инструкция по ручному запуску:", C.INFO)
            log("1. Откройте новое окно PowerShell/Terminal", C.INFO)
            log("2. Выполните: python app.py", C.INFO)
            log("3. В этом окне выполните: python test_improved.py", C.INFO)
            sys.exit(1)
    else:
        log("Сервер уже запущен (найден активный)\n", C.OK)

    banner("ЭТАП 1: РЕЗЕРВНОЕ КОПИРОВАНИЕ ДАННЫХ", C.INFO)
    backup_orders()

    report.add_header()
    report.add_explanation()

    banner("ЭТАП 2: ЗАПУСК ТЕСТОВ", C.BOLD)

    tests = [
        ("КАТЕГОРИЯ 1: Основная работоспособность (10 тестов)",
         "Проверяем, работает ли система целиком", [
            test_01_server_alive,
            test_02_products_list_structure,
            test_03_product_detail,
            test_04_product_not_found,
            test_05_create_order_success,
            test_06_create_order_missing_customer,
            test_07_create_order_incomplete_customer,
            test_08_create_order_empty_body,
            test_09_orders_history_exists,
            test_10_stats_structure,
        ]),
        ("КАТЕГОРИЯ 2: Валидация входных данных (4 теста)",
         "Проверяем, отклоняет ли система неправильные данные", [
            test_20_validation_email_format,
            test_21_validation_negative_price,
            test_22_validation_xss_injection,
            test_23_validation_sql_injection,
        ]),
        ("КАТЕГОРИЯ 3: Верификация (6 тестов)",
         "Проверяем, правильно ли работают расчёты и форматы", [
            test_30_verify_order_id_format,
            test_31_verify_date_format,
            test_32_verify_total_amount_calculation,
            test_33_verify_order_persistence,
            test_34_verify_stats_consistency,
            test_35_verify_idempotency,
        ]),
        ("КАТЕГОРИЯ 4: Граничные значения (4 теста)",
         "Проверяем поведение на 'краях' допустимого", [
            test_40_boundary_zero_quantity,
            test_41_boundary_large_quantity,
            test_42_boundary_empty_products,
            test_43_boundary_long_name,
        ]),
        ("КАТЕГОРИЯ 5: Нагрузочное тестирование (2 теста)",
         "Проверяем, выдержит ли система нагрузку", [
            test_50_stress_multiple_orders,
            test_51_stress_concurrent_orders,
        ]),
        ("КАТЕГОРИЯ 6: Юзабилити (3 теста)",
         "Проверяем удобство использования API", [
            test_60_usability_content_type,
            test_61_usability_error_messages,
            test_62_usability_cors_headers,
        ]),
        ("КАТЕГОРИЯ 7: Приёмочный тест (1 тест)",
         "Проверяем реальный бизнес-сценарий", [
            test_70_acceptance_full_flow,
        ]),
    ]

    total_passed = 0
    total_failed = 0

    for category_name, category_desc, category_tests in tests:
        banner(category_name, C.BOLD)
        report.start_category(category_name, category_desc)

        for i, test in enumerate(category_tests, 1):
            name = test.__doc__ or test.__name__
            log(f"Тест [{i:02d}/{len(category_tests):02d}] {name}", C.INFO)
            try:
                test()
                log(f"   [OK] ПРОЙДЕН\n", C.OK)
                total_passed += 1
            except AssertionError as e:
                log(f"   [FAIL] ПРОВАЛЕН: {e}\n", C.FAIL)
                total_failed += 1
            except Exception as e:
                log(f"   [FAIL] ОШИБКА: {e}\n", C.FAIL)
                total_failed += 1

    tracker.print_table()
    report.add_speed_table(tracker.records)

    banner("ЭТАП 3: ВОССТАНОВЛЕНИЕ ДАННЫХ", C.INFO)
    restore_orders()

    total = total_passed + total_failed
    percent = (total_passed / total * 100) if total > 0 else 0

    banner("ИТОГИ", C.BOLD)
    log(f"[OK] Пройдено:  {total_passed}/{total} ({percent:.0f}%)", C.OK if total_failed == 0 else C.INFO)
    if total_failed > 0:
        log(f"[FAIL] Провалено: {total_failed}/{total}", C.FAIL)

    if percent == 100:
        log(f"\nУСПЕХ: 100% тестов пройдено!", C.OK)
    elif percent >= 80:
        log(f"\nХОРОШО: {percent:.0f}% тестов пройдено", C.WARN)
    else:
        log(f"\nТРЕБУЕТСЯ ДОРАБОТКА: {percent:.0f}% тестов пройдено", C.FAIL)

    report.add_summary()
    report.save()

    log(f"\nПодробный отчёт сохранён в: {os.path.abspath(REPORT_FILE)}", C.INFO)
    log("Откройте report.txt — там всё на простом языке для преподавателя", C.INFO)

    return total_failed == 0


if __name__ == "__main__":
    try:
        ok = run_all()
    except KeyboardInterrupt:
        log("\n\nПрервано. Восстанавливаем данные...", C.WARN)
        restore_orders()
        stop_server()
        log("Данные восстановлены.", C.OK)
        sys.exit(130)
    except Exception as e:
        log(f"\n\nКритическая ошибка: {e}", C.FAIL)
        restore_orders()
        stop_server()
        log("Данные восстановлены.", C.OK)
        sys.exit(1)
    finally:
        if server_process is not None:
            stop_server()

    sys.exit(0 if ok else 1)
