#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import webbrowser

GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RED = '\033[91m'
NC = '\033[0m'

def print_color(text, color=BLUE): print(f"{color}{text}{NC}")
def print_step(text): print_color(f"▶ {text}", YELLOW)
def print_success(text): print_color(f"✓ {text}", GREEN)
def print_error(text): print_color(f"✗ {text}", RED)

def check_python():
    if sys.version_info < (3, 8):
        print_error("Требуется Python 3.8+")
        sys.exit(1)
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}")

def setup_venv():
    print_step("Настройка виртуального окружения...")
    if not os.path.exists("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Виртуальное окружение создано")
    else:
        print_success("Виртуальное окружение уже существует")
    if sys.platform == "win32":
        pip_path = os.path.join("venv", "Scripts", "pip")
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    return pip_path, python_path

def install_dependencies(pip_path):
    print_step("Установка зависимостей...")
    packages = ["flask", "aiogram", "aiosqlite", "requests", "names"]
    for pkg in packages:
        print(f"  📦 {pkg}...")
        subprocess.run([pip_path, "install", pkg], capture_output=True)
    print_success("Зависимости установлены")

def init_database(python_path):
    print_step("Инициализация БД...")
    if os.path.exists("generate_test_data.py"):
        subprocess.run([python_path, "generate_test_data.py"])
    else:
        # минимальная инициализация
        code = '''
import aiosqlite, asyncio
async def init():
    async with aiosqlite.connect('cargo.db') as db:
        await db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT, work_type TEXT, scheduled_date TEXT, scheduled_time TEXT, address TEXT, comment TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, cost REAL)")
        await db.execute("CREATE TABLE IF NOT EXISTS loaders (user_id INTEGER PRIMARY KEY, full_name TEXT, phone TEXT, is_active INTEGER, total_orders INTEGER, total_earnings REAL, rating REAL)")
        await db.execute("CREATE TABLE IF NOT EXISTS transport (id INTEGER PRIMARY KEY, name TEXT, type TEXT, capacity TEXT, is_available INTEGER)")
        await db.commit()
asyncio.run(init())
'''
        with open("_temp_init.py","w") as f: f.write(code)
        subprocess.run([python_path, "_temp_init.py"])
        os.remove("_temp_init.py")
    print_success("База данных готова")

def run_services(python_path):
    processes = []
    # бот
    bot_proc = subprocess.Popen([python_path, "bot.py"], stdout=open("bot.log","w"), stderr=subprocess.STDOUT)
    processes.append(("бот", bot_proc))
    print_success(f"Бот запущен (PID: {bot_proc.pid})")
    time.sleep(2)
    # сайт
    site_proc = subprocess.Popen([python_path, "website.py"], stdout=open("website.log","w"), stderr=subprocess.STDOUT)
    processes.append(("сайт", site_proc))
    print_success(f"Сайт запущен (PID: {site_proc.pid})")
    return processes

def create_shortcut():
    if sys.platform == "win32":
        with open("start.bat","w") as f:
            f.write('@echo off\ncd /d "%~dp0"\npython launch.py\npause')
        print_success("Создан start.bat")
    else:
        with open("start.sh","w") as f:
            f.write('#!/bin/bash\ncd "$(dirname "$0")"\npython3 launch.py\n')
        os.chmod("start.sh", 0o755)
        print_success("Создан start.sh")

def main():
    print("\n"+"="*60)
    print("🚚 ЗАПУСК СИСТЕМЫ ГРУЗОПЕРЕВОЗОК")
    print("="*60+"\n")
    check_python()
    pip_path, python_path = setup_venv()
    install_dependencies(pip_path)
    init_database(python_path)
    procs = run_services(python_path)
    create_shortcut()
    print("\n✅ Система запущена!")
    print("🌐 Сайт: http://localhost:5000")
    print("👑 Админ: http://localhost:5000/admin (пароль 14881488)")
    print("📁 Логи: bot.log, website.log")
    print("📱 Telegram бот: @gruzexpert_bot (замените ссылку в боте и на сайте)")
    print("\nНажмите Ctrl+C для остановки\n")
    try:
        for _, p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("\n⏹ Остановка...")
        for _, p in procs:
            p.terminate()
        print_success("Остановлено")

if __name__ == "__main__":
    main()
