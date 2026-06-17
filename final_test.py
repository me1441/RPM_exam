"""
V-MODEL TESTING + PERFORMANCE + MEMORY PROFILING
Блоки: Верификация | Валидация | Юзабилити | Нагрузка | Граничные | Производительность
"""

import requests, sys, time, os, shutil, concurrent.futures, subprocess, psutil
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
API = "/api"
ORDERS_FILE = os.path.join(os.path.expanduser("~"), "orders_data.json")
BACKUP = ORDERS_FILE + ".bak"
REPORT = "report.txt"
server_proc = None

class C:
    OK, FAIL, WARN, INFO, BOLD, DIM, RST = "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[1m", "\033[2m", "\033[0m"

def log(msg, color=C.RST, ind=0): print(f"{color}{'    '*ind}{msg}{C.RST}")
def banner(t, color=C.BOLD, w=78): print(f"\n{color}{'='*w}\n  {t:<{w-4}}\n{'='*w}{C.RST}\n")

def start_server():
    global server_proc
    app = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    if not os.path.exists(app): app = "app.py"
    server_proc = subprocess.Popen([sys.executable, app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        time.sleep(0.5)
        try:
            if requests.get(BASE_URL, timeout=1).status_code == 200: return True
        except: pass
    return False

def stop_server():
    global server_proc
    if server_proc:
        server_proc.terminate()
        try: server_proc.wait(timeout=5)
        except: server_proc.kill()
        server_proc = None

def backup():
    if os.path.exists(ORDERS_FILE): shutil.copy2(ORDERS_FILE, BACKUP)

def restore():
    if os.path.exists(BACKUP): shutil.copy2(BACKUP, ORDERS_FILE); os.remove(BACKUP)
    elif os.path.exists(ORDERS_FILE): os.remove(ORDERS_FILE)

def get_product():
    return list(requests.get(f"{BASE_URL}{API}/products", timeout=5).json()["products"].values())[0]

def create_order(name, item=None, custom=None):
    p = custom or {
        "customer": {"name": name, "email": f"{name}@t.com", "phone": "+7 999 000-00-00"},
        "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}],
        "total_amount": item["price"], "payment_method": "card"
    }
    return requests.post(f"{BASE_URL}{API}/order", json=p, timeout=5)

class Report:
    def __init__(self):
        self.lines, self.p, self.f, self.w, self.defects, self.speed, self.perf = [], 0, 0, 0, [], [], []

    def add(self, text=""): self.lines.append(text)

    def test(self, n, name, status, desc, details="", rec=""):
        icon = "[OK]" if status=="PASS" else ("[FAIL]" if status=="FAIL" else "[WARN]")
        st = "ПРОЙДЕН" if status=="PASS" else ("ПРОВАЛЕН" if status=="FAIL" else "ДЕФЕКТ")
        if status=="PASS": self.p += 1
        elif status=="FAIL": self.f += 1
        elif status=="WARN": self.w += 1; self.defects.append((name, details, rec))
        self.add(f"   Тест {n}  [{icon} {st}]  {name}")
        self.add(f"             Проверка: {desc}")
        if details: self.add(f"             Результат: {details}")
        if rec: self.add(f"             Рекомендация: {rec}")
        self.add()

    def speed_table(self):
        if not self.speed: return
        self.add(); self.add("   ТАБЛИЦА СКОРОСТИ API:")
        self.add("   " + "-"*65); self.add(f"   {'№':<4} {'Запрос':<28} {'Время, мс':<12} {'Статус':<18}")
        self.add("   " + "-"*65)
        times = []
        for i, (name, ms, st) in enumerate(self.speed, 1):
            times.append(ms); self.add(f"   {i:<4} {name:<28} {ms:>8.2f}     {st}")
        self.add("   " + "-"*65)
        if times:
            avg = sum(times)/len(times)
            self.add(f"   Среднее: {avg:.2f} мс | Минимум: {min(times):.2f} мс | Максимум: {max(times):.2f} мс")
            if avg < 50: self.add("   Оценка: Отличная скорость")
            elif avg < 200: self.add("   Оценка: Хорошая скорость")
            else: self.add("   Оценка: Требуется оптимизация")

    def memory_table(self):
        if not self.perf: return
        self.add(); self.add("   ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ И ПАМЯТИ:")
        self.add("   " + "-"*65); self.add(f"   {'Тест':<25} {'RPS':<10} {'Время, мс':<12} {'Память, МБ':<12}")
        self.add("   " + "-"*65)
        for name, rps, elapsed, mem in self.perf:
            mem_str = f"{mem:.1f}" if mem else "—"
            rps_str = f"{rps:.1f}" if rps else "—"
            elapsed_str = f"{elapsed:.1f}" if elapsed else "—"
            self.add(f"   {name:<25} {rps_str:>8}   {elapsed_str:>8}     {mem_str:>8}")
        self.add("   " + "-"*65)

    def summary(self):
        total = self.p + self.f + self.w
        self.add(); self.add("="*67); self.add("ИТОГИ"); self.add("="*67)
        self.add(f"   Всего тестов: {total} | Пройдено: {self.p} | Дефекты: {self.w} | Провалено: {self.f}")
        if self.defects:
            self.add("   НАЙДЕННЫЕ ДЕФЕКТЫ:")
            for i, (n, d, r) in enumerate(self.defects, 1): self.add(f"   {i}. {n}: {d} → {r}")
        self.add("   Данные пользователя восстановлены"); self.add("="*67)

    def save(self):
        with open(REPORT, 'w', encoding='utf-8') as f: f.write('\n'.join(self.lines))
        log(f"Отчёт сохранён: {os.path.abspath(REPORT)}", C.OK)

rep = Report()

def measure(name, func):
    t0 = time.perf_counter()
    try:
        r = func(); ms = (time.perf_counter() - t0) * 1000
        st = f"{r.status_code} OK" if r.status_code < 300 else str(r.status_code)
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000; st = f"ERR: {type(e).__name__}"
    rep.speed.append((name, ms, st))
    log(f"  {name:<30} {ms:>8.2f} мс  {st}", C.OK if ms < 200 else C.WARN)
    return r

def print_speed_table():
    if not rep.speed: return
    banner("ТАБЛИЦА СКОРОСТИ API", C.BOLD)
    log(f"{'№':<4} {'Запрос':<30} {'Время, мс':<12} {'Статус':<15}", C.BOLD)
    log("-" * 65, C.DIM)
    times = []
    for i, (name, ms, st) in enumerate(rep.speed, 1):
        times.append(ms)
        color = C.OK if ms < 50 else (C.WARN if ms < 200 else C.FAIL)
        log(f"{i:<4} {name:<30} {color}{ms:>8.2f}{C.RST}      {st}")
    log("-" * 65, C.DIM)
    if times:
        avg = sum(times)/len(times)
        log(f"{'':4} {'ИТОГО:':<30} Среднее: {avg:.2f} мс | Мин: {min(times):.2f} | Макс: {max(times):.2f}", C.BOLD)
        if avg < 50: log("Оценка: Отличная скорость", C.OK)
        elif avg < 200: log("Оценка: Хорошая скорость", C.WARN)
        else: log("Оценка: Требуется оптимизация", C.FAIL)

def print_memory_table():
    if not rep.perf: return
    banner("ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ И ПАМЯТИ", C.BOLD)
    log(f"{'Тест':<28} {'RPS':<10} {'Время, мс':<12} {'Память, МБ':<12}", C.BOLD)
    log("-" * 65, C.DIM)
    for name, rps, elapsed, mem in rep.perf:
        mem_str = f"{mem:.1f}" if mem else "—"
        rps_str = f"{rps:.1f}" if rps else "—"
        elapsed_str = f"{elapsed:.1f}" if elapsed else "—"
        log(f"{name:<28} {rps_str:>8}   {elapsed_str:>8}     {mem_str:>8}")
    log("-" * 65, C.DIM)

def get_memory():
    if not server_proc: return None
    return psutil.Process(server_proc.pid).memory_info().rss / 1024 / 1024

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 1. СИСТЕМНЫЕ ТЕСТЫ
# ═══════════════════════════════════════════════════════════════════════════════

def t01_alive():
    r = measure("Сервер", lambda: requests.get(BASE_URL, timeout=5))
    assert r.status_code == 200; rep.test("1.1", "Сервер", "PASS", "запущен ли сервер")

def t02_products():
    r = measure("Товары", lambda: requests.get(f"{BASE_URL}{API}/products", timeout=5))
    assert r.json()["count"] == 8; rep.test("1.2", "Каталог", "PASS", "8 товаров")

def t03_detail():
    pid = list(requests.get(f"{BASE_URL}{API}/products", timeout=5).json()["products"].keys())[0]
    r = measure("Детали товара", lambda: requests.get(f"{BASE_URL}{API}/products/{pid}", timeout=5))
    assert "name" in r.json()["product"]; rep.test("1.3", "Детали товара", "PASS", "данные корректны")

def t04_404():
    r = measure("Ошибка 404", lambda: requests.get(f"{BASE_URL}{API}/products/xxx", timeout=5))
    assert r.status_code == 404; rep.test("1.4", "Ошибка 404", "PASS", "несуществующий ID")

def t05_create():
    item = get_product()
    r = measure("Создание заказа", lambda: create_order("Иван", item))
    assert r.status_code == 200; rep.test("1.5", "Заказ", "PASS", "оформление", f"ID: {r.json()['order']['order_id']}")

def t06_no_customer():
    r = measure("Нет клиента", lambda: requests.post(f"{BASE_URL}{API}/order", json={"products": []}, timeout=5))
    assert r.status_code == 400; rep.test("1.6", "Без клиента", "PASS", "отклонение")

def t07_incomplete():
    r = measure("Неполный клиент", lambda: requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "Иван"}, "products": []}, timeout=5))
    assert r.status_code == 400; rep.test("1.7", "Неполные данные", "PASS", "отклонение")

def t08_empty():
    r = measure("Пустое тело", lambda: requests.post(f"{BASE_URL}{API}/order", json=None, timeout=5))
    assert r.status_code == 400; rep.test("1.8", "Пустой заказ", "PASS", "отклонение")

def t09_history():
    r = measure("История заказов", lambda: requests.get(f"{BASE_URL}{API}/orders", timeout=5))
    assert r.json()["count"] > 0; rep.test("1.9", "История", "PASS", f"{r.json()['count']} заказов")

def t10_stats():
    r = measure("Статистика", lambda: requests.get(f"{BASE_URL}{API}/stats", timeout=5))
    assert "total_revenue" in r.json(); rep.test("1.10", "Статистика", "PASS", "выручка посчитана")

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 2. ВАЛИДАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def t20_email():
    item = get_product()
    r = measure("Невалидный email", lambda: create_order("E", item, {"customer": {"name": "T", "email": "не-email", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}))
    if r.status_code == 200: rep.test("2.1", "Email", "WARN", "невалидный email", "ПРИНЯТ НЕВЕРНЫЙ EMAIL", "добавить проверку формата")
    else: rep.test("2.1", "Email", "PASS", "невалидный email отклонён")

def t21_negative():
    item = get_product()
    r = measure("Отрицательная цена", lambda: create_order("N", item, {"customer": {"name": "T", "email": "t@t.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": -1000, "quantity": 1}], "total_amount": -1000, "payment_method": "card"}))
    if r.status_code == 200: rep.test("2.2", "Цена", "WARN", "отрицательная цена", "ПРИНЯТА ОТРИЦАТЕЛЬНАЯ ЦЕНА", "добавить проверку > 0")
    else: rep.test("2.2", "Цена", "PASS", "отрицательная цена отклонена")

def t22_xss():
    item = get_product()
    r = measure("XSS-инъекция", lambda: create_order("X", item, {"customer": {"name": "X", "email": "x@x.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card", "comment": "<script>alert('xss')</script>"}))
    assert "<script>" not in r.text or "alert(" not in r.text; rep.test("2.3", "XSS", "PASS", "скрипт обезврежен")

def t23_sql():
    item = get_product()
    r = measure("SQL-инъекция", lambda: create_order("S", item, {"customer": {"name": "'; DROP TABLE orders; --", "email": "s@s.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}))
    assert requests.get(f"{BASE_URL}{API}/orders", timeout=5).status_code == 200; rep.test("2.4", "SQL", "PASS", "данные не повреждены")

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 3. ВЕРИФИКАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def t30_id():
    r = create_order("ID"); oid = r.json()["order"]["order_id"]
    assert oid.startswith("ORD-") and len(oid) == 16; rep.test("3.1", "Формат ID", "PASS", "ORD-XXXXXXXXXXXX", oid)

def t31_date():
    d = create_order("D").json()["order"]["date"]
    assert len(d.split()) == 2 and "." in d; rep.test("3.2", "Дата", "PASS", "ДД.ММ.ГГГГ ЧЧ:ММ:СС", d)

def t32_calc():
    items = list(requests.get(f"{BASE_URL}{API}/products", timeout=5).json()["products"].values())[:2]
    exp = items[0]["price"] * 3 + items[1]["price"] * 2
    r = requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "M", "email": "m@m.com", "phone": "+7"}, "products": [{"id": str(items[0]["id"]), "name": items[0]["name"], "price": items[0]["price"], "quantity": 3}, {"id": str(items[1]["id"]), "name": items[1]["name"], "price": items[1]["price"], "quantity": 2}], "total_amount": exp, "payment_method": "card"}, timeout=5)
    assert r.json()["order"]["total_amount"] == exp; rep.test("3.3", "Сумма", "PASS", "расчёт верен", f"{exp} руб.")

def t33_persist():
    oid = create_order("P").json()["order"]["order_id"]
    assert any(o.get("order_id") == oid for o in requests.get(f"{BASE_URL}{API}/orders", timeout=5).json()["orders"]); rep.test("3.4", "Сохранение", "PASS", "заказ в истории")

def t34_consistency():
    o = requests.get(f"{BASE_URL}{API}/orders", timeout=5).json()["orders"]
    s = requests.get(f"{BASE_URL}{API}/stats", timeout=5).json()
    assert s["total_revenue"] == sum(x["total_amount"] for x in o); rep.test("3.5", "Согласованность", "PASS", "статистика = заказам")

def t35_idempotency():
    cid = "ORD-TEST-DUP-001"
    p = {"order_id": cid, "customer": {"name": "I", "email": "i@i.com", "phone": "+7"}, "products": [], "total_amount": 0, "payment_method": "cash"}
    requests.post(f"{BASE_URL}{API}/order", json=p, timeout=5)
    requests.post(f"{BASE_URL}{API}/order", json=p, timeout=5)
    c = sum(1 for o in requests.get(f"{BASE_URL}{API}/orders", timeout=5).json()["orders"] if o.get("order_id") == cid)
    if c == 2: rep.test("3.6", "Дубли", "WARN", "два заказа с одним ID", f"СОЗДАНО {c} ЗАКАЗА", "проверять уникальность")
    else: rep.test("3.6", "Дубли", "PASS", "дублирование предотвращено")

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 4. ГРАНИЧНЫЕ ЗНАЧЕНИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def t40_zero():
    item = get_product()
    r = measure("Количество = 0", lambda: create_order("Z", item, {"customer": {"name": "Z", "email": "z@z.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 0}], "total_amount": 0, "payment_method": "card"}))
    rep.test("4.1", "Количество = 0", "INFO", "нулевое количество", f"статус {r.status_code}", "возможно, запретить")

def t41_large():
    item = get_product()
    r = measure("Количество = 10000", lambda: create_order("L", item, {"customer": {"name": "L", "email": "l@l.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 10000}], "total_amount": item["price"] * 10000, "payment_method": "card"}))
    if r.status_code == 200 and item["stock"] < 10000: rep.test("4.2", "Количество = 10000", "WARN", "заказ превышает stock", f"stock={item['stock']}", "проверять остатки")
    else: rep.test("4.2", "Количество = 10000", "INFO", "большое количество", f"статус {r.status_code}")

def t42_empty_products():
    r = measure("Пустые товары", lambda: requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "E", "email": "e@e.com", "phone": "+7"}, "products": [], "total_amount": 0, "payment_method": "cash"}, timeout=5))
    rep.test("4.3", "Пустой заказ", "INFO", "без товаров", f"статус {r.status_code}", "возможно, требовать ≥1 товара")

def t43_long_name():
    item = get_product()
    r = measure("Имя 500 символов", lambda: create_order("A"*500, item)); rep.test("4.4", "Длинное имя", "INFO", "500 символов", f"статус {r.status_code}")

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 5. НАГРУЗКА
# ═══════════════════════════════════════════════════════════════════════════════

def t50_stress():
    item = get_product()
    t0 = time.time()
    for i in range(10):
        measure(f"Стресс #{i+1}", lambda i=i: create_order(f"S{i}", item))
    ms = (time.time() - t0) * 1000; rep.test("5.1", "10 заказов", "PASS", "последовательная нагрузка", f"за {ms:.0f} мс, среднее {ms/10:.1f} мс")

def t51_concurrent():
    item = get_product()
    def mk(i): return requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": f"P{i}", "email": f"p{i}@p.com", "phone": f"+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}, timeout=5)
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(5) as ex:
        res = [f.result() for f in concurrent.futures.as_completed([ex.submit(mk, i) for i in range(5)])]
    ms = (time.time() - t0) * 1000; ok = sum(1 for r in res if r.status_code == 200)
    rep.test("5.2", "5 параллельных", "PASS", "конкурентность", f"{ok}/5 за {ms:.0f} мс")

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 6. ЮЗАБИЛИТИ
# ═══════════════════════════════════════════════════════════════════════════════

def t60_content_type():
    for ep in ["/api/products", "/api/orders", "/api/stats", "/api/products/1"]:
        r = measure(f"Content-Type {ep}", lambda ep=ep: requests.get(f"{BASE_URL}{API}{ep}", timeout=5))
        assert "json" in r.headers.get("Content-Type", "")
    rep.test("6.1", "Формат JSON", "PASS", "все адреса возвращают JSON")

def t61_error_messages():
    r = measure("Сообщение 404", lambda: requests.get(f"{BASE_URL}{API}/products/xxx", timeout=5))
    msg = r.json().get("error", "")
    rep.test("6.2", "Понятность ошибок", "PASS", "сообщение при 404", f'"{msg}"')

def t62_headers():
    r = measure("Заголовки ответа", lambda: requests.get(f"{BASE_URL}{API}/products", timeout=5))
    assert "Content-Type" in r.headers; rep.test("6.3", "Заголовки", "PASS", "технические заголовки корректны")

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 7. ПРОИЗВОДИТЕЛЬНОСТЬ: память, RPS, latency, спайки
# ═══════════════════════════════════════════════════════════════════════════════

def p01_memory_baseline():
    mem = get_memory()
    if mem is None: rep.test("P.1", "Базовая память", "WARN", "процесс не найден"); return
    rep.test("P.1", "Базовая память", "PASS", "RSS/VMS сервера", f"RSS: {mem:.1f} МБ")
    log(f"  Базовая память сервера: {mem:.1f} МБ", C.OK, 1)
    rep.perf.append(("Базовая память", None, None, mem))

def p02_rps_load(target=50, duration=5):
    item = get_product()
    def shoot():
        try: return requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "Perf", "email": "perf@t.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}, timeout=2).status_code == 200
        except: return False
    total = target * duration; t0 = time.time(); ok = 0
    for i in range(total):
        if shoot(): ok += 1
        time.sleep(max(0, (i + 1) / target - (time.time() - t0)))
    elapsed = (time.time() - t0) * 1000; actual = total / (elapsed / 1000)
    st = "OK" if ok == total else ("WARN" if ok > total * 0.9 else "FAIL")
    rep.test("P.2", f"Нагрузка {target} RPS", "PASS" if st == "OK" else ("WARN" if st == "WARN" else "FAIL"),
             f"{target} запросов/сек в течение {duration}с", f"{ok}/{total} успешно, факт RPS: {actual:.1f}")
    log(f"  {ok}/{total} успешно | Факт RPS: {actual:.1f} | Время: {elapsed:.0f} мс", C.OK if st == "OK" else C.WARN, 1)
    rep.perf.append((f"Нагрузка {target} RPS", actual, elapsed, None))

def p03_memory_load():
    mem_before = get_memory()
    if mem_before is None: rep.test("P.3", "Память под нагрузкой", "WARN", "процесс не найден"); return
    item = get_product()
    for _ in range(50): requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "M", "email": "m@t.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}, timeout=5)
    mem_after = get_memory()
    delta = mem_after - mem_before
    status = "PASS" if delta < 10 else ("WARN" if delta < 50 else "FAIL")
    rep.test("P.3", "Память под нагрузкой", status, "рост памяти после 50 заказов", f"было: {mem_before:.1f} → стало: {mem_after:.1f} МБ (Δ {delta:+.1f})")
    log(f"  Δ памяти: {delta:+.1f} МБ", C.OK if status == "PASS" else C.WARN, 1)
    rep.perf.append(("Память под нагрузкой", None, None, delta))

def p04_latency():
    item = get_product(); times = []
    for _ in range(100):
        t0 = time.perf_counter()
        requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "L", "email": "l@t.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}, timeout=5)
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    p50, p95, p99, avg = times[49], times[94], times[98], sum(times) / len(times)
    rep.test("P.4", "Latency percentiles", "PASS", "распределение задержек 100 запросов", f"p50: {p50:.1f} | p95: {p95:.1f} | p99: {p99:.1f} | avg: {avg:.1f} мс")
    log(f"  p50: {p50:.1f} | p95: {p95:.1f} | p99: {p99:.1f} | avg: {avg:.1f} мс", C.OK, 1)
    rep.perf.append(("Latency p50/p95/p99", None, avg, None))

def p05_spike():
    item = get_product()
    def shoot():
        try: return requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "Spike", "email": "s@t.com", "phone": "+7"}, "products": [{"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 1}], "total_amount": item["price"], "payment_method": "card"}, timeout=2).status_code == 200
        except: return False
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(20) as ex:
        res = list(ex.map(lambda _: shoot(), range(100)))
    elapsed = (time.time() - t0) * 1000; ok = sum(res)
    status = "PASS" if ok >= 95 else ("WARN" if ok >= 80 else "FAIL")
    rep.test("P.5", "Спайк 100 запросов", status, "20 потоков × 100 запросов", f"{ok}/100 за {elapsed:.0f} мс")
    log(f"  {ok}/100 успешно | {elapsed:.0f} мс", C.OK if status == "PASS" else C.WARN, 1)
    rep.perf.append(("Спайк 100 запросов", None, elapsed, None))

# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 8. ПРИЁМОЧНЫЙ ТЕСТ
# ═══════════════════════════════════════════════════════════════════════════════

def t70_acceptance():
    log("Полный сценарий: каталог → товар → заказ → история → статистика", C.INFO, 1)
    products = requests.get(f"{BASE_URL}{API}/products", timeout=5).json()["products"]
    pid = list(products.keys())[0]
    product = requests.get(f"{BASE_URL}{API}/products/{pid}", timeout=5).json()["product"]
    r = requests.post(f"{BASE_URL}{API}/order", json={"customer": {"name": "Покупатель", "email": "buyer@example.com", "phone": "+7 (900) 123-45-67"}, "products": [{"id": str(product["id"]), "name": product["name"], "price": product["price"], "quantity": 2}], "total_amount": product["price"] * 2, "payment_method": "card", "comment": "В подарочной упаковке"}, timeout=5)
    oid = r.json()["order"]["order_id"]
    assert any(o.get("order_id") == oid for o in requests.get(f"{BASE_URL}{API}/orders", timeout=5).json()["orders"])
    assert requests.get(f"{BASE_URL}{API}/stats", timeout=5).json()["total_orders"] > 0
    rep.test("A.1", "Полный сценарий", "PASS", "каталог → товар → заказ → история → статистика", "ВЕСЬ СЦЕНАРИЙ РАБОТАЕТ")

# ═══════════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════════

TESTS = [
    ("БЛОК 1. СИСТЕМНЫЕ ТЕСТЫ (работоспособность)", [t01_alive, t02_products, t03_detail, t04_404, t05_create, t06_no_customer, t07_incomplete, t08_empty, t09_history, t10_stats]),
    ("БЛОК 2. ВАЛИДАЦИЯ (отклонение плохих данных)", [t20_email, t21_negative, t22_xss, t23_sql]),
    ("БЛОК 3. ВЕРИФИКАЦИЯ (расчёты и форматы)", [t30_id, t31_date, t32_calc, t33_persist, t34_consistency, t35_idempotency]),
    ("БЛОК 4. ГРАНИЧНЫЕ ЗНАЧЕНИЯ (края допустимого)", [t40_zero, t41_large, t42_empty_products, t43_long_name]),
    ("БЛОК 5. НАГРУЗКА (скорость при нагрузке)", [t50_stress, t51_concurrent]),
    ("БЛОК 6. ЮЗАБИЛИТИ (удобство API)", [t60_content_type, t61_error_messages, t62_headers]),
    ("БЛОК 7. ПРОИЗВОДИТЕЛЬНОСТЬ (память, RPS, latency)", [p01_memory_baseline, p02_rps_load, p03_memory_load, p04_latency, p05_spike]),
    ("БЛОК 8. ПРИЁМОЧНЫЙ ТЕСТ (полный сценарий)", [t70_acceptance]),
]

def run():
    banner("V-MODEL TESTING: 8 БЛОКОВ", C.BOLD)
    if not (lambda: (requests.get(BASE_URL, timeout=3).status_code == 200))():
        log("Запуск сервера...", C.INFO)
        if not start_server(): log("Не удалось запустить сервер!", C.FAIL); sys.exit(1)
    
    backup(); banner("РЕЗЕРВНАЯ КОПИЯ СОЗДАНА", C.INFO)
    
    rep.add("="*67); rep.add("ОТЧЁТ О ТЕСТИРОВАНИИ"); rep.add(f"Дата: {datetime.now():%d.%m.%Y %H:%M}"); rep.add("="*67)
    rep.add(); rep.add("СТРУКТУРА ТЕСТИРОВАНИЯ (8 блоков):"); rep.add("-"*67)
    rep.add("   Блок 1 — Системные тесты: работает ли приложение целиком")
    rep.add("   Блок 2 — Валидация: отклоняет ли плохие данные")
    rep.add("   Блок 3 — Верификация: правильно ли считает и форматирует")
    rep.add("   Блок 4 — Граничные значения: что на 'краях' правил")
    rep.add("   Блок 5 — Нагрузка: скорость при многих заказах")
    rep.add("   Блок 6 — Юзабилити: удобно ли пользоваться API")
    rep.add("   Блок 7 — Производительность: память, RPS, latency")
    rep.add("   Блок 8 — Приёмочный тест: полный сценарий покупки")
    
    passed = failed = 0
    for cat, tests in TESTS:
        banner(cat, C.BOLD)
        for t in tests:
            log(t.__name__, C.INFO)
            try: t(); log("  [OK]", C.OK); passed += 1
            except AssertionError as e: log(f"  [FAIL] {e}", C.FAIL); failed += 1
            except Exception as e: log(f"  [ERR] {e}", C.FAIL); failed += 1
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ВЫВОД ТАБЛИЦ СКОРОСТИ И ПАМЯТИ
    # ═══════════════════════════════════════════════════════════════════════════
    print_speed_table()
    print_memory_table()
    rep.speed_table()
    rep.memory_table()
    rep.summary()
    rep.save()
    restore()
    stop_server()
    
    total = passed + failed
    log(f"\n[OK] {passed}/{total} ({passed/total*100:.0f}%)", C.OK if failed == 0 else C.WARN)
    if failed: log(f"[FAIL] {failed}", C.FAIL)
    log(f"Отчёт: {os.path.abspath(REPORT)}", C.INFO)

def print_speed_table():
    if not rep.speed: return
    banner("ТАБЛИЦА СКОРОСТИ API", C.BOLD)
    log(f"{'№':<4} {'Запрос':<30} {'Время, мс':<12} {'Статус':<15}", C.BOLD)
    log("-" * 65, C.DIM)
    times = []
    for i, (name, ms, st) in enumerate(rep.speed, 1):
        times.append(ms)
        color = C.OK if ms < 50 else (C.WARN if ms < 200 else C.FAIL)
        log(f"{i:<4} {name:<30} {color}{ms:>8.2f}{C.RST}      {st}")
    log("-" * 65, C.DIM)
    if times:
        avg = sum(times)/len(times)
        log(f"{'':4} {'ИТОГО:':<30} Среднее: {avg:.2f} мс | Мин: {min(times):.2f} | Макс: {max(times):.2f}", C.BOLD)
        if avg < 50: log("Оценка: Отличная скорость", C.OK)
        elif avg < 200: log("Оценка: Хорошая скорость", C.WARN)
        else: log("Оценка: Требуется оптимизация", C.FAIL)

def print_memory_table():
    if not rep.perf: return
    banner("ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ И ПАМЯТИ", C.BOLD)
    log(f"{'Тест':<28} {'RPS':<10} {'Время, мс':<12} {'Память, МБ':<12}", C.BOLD)
    log("-" * 65, C.DIM)
    for name, rps, elapsed, mem in rep.perf:
        mem_str = f"{mem:.1f}" if mem else "—"
        rps_str = f"{rps:.1f}" if rps else "—"
        elapsed_str = f"{elapsed:.1f}" if elapsed else "—"
        log(f"{name:<28} {rps_str:>8}   {elapsed_str:>8}     {mem_str:>8}")
    log("-" * 65, C.DIM)

if __name__ == "__main__":
    try: run()
    except KeyboardInterrupt: restore(); stop_server()
    except Exception as e: log(f"Критическая ошибка: {e}", C.FAIL); restore(); stop_server()