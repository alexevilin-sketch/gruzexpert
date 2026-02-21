#!/usr/bin/env python3
import aiosqlite
import asyncio
import random
import string
from datetime import datetime, timedelta

async def generate():
    async with aiosqlite.connect('cargo.db') as db:
        # Очистка таблиц (для теста можно закомментировать)
        await db.execute('DELETE FROM orders')
        await db.execute('DELETE FROM loaders')
        await db.execute('DELETE FROM transport')

        # Работники
        names = ["Иван Петров", "Петр Сидоров", "Анна Иванова", "Ольга Смирнова", "Дмитрий Козлов", "Елена Васильева", "Сергей Новиков"]
        for i, name in enumerate(names):
            uid = 2000 + i
            await db.execute('''INSERT INTO loaders (user_id, full_name, phone, is_active, total_orders, total_earnings, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (uid, name, f"+3706{random.randint(1000000,9999999)}", 1, random.randint(5,50), random.uniform(500,5000), round(random.uniform(4.5,5.0),1)))
        # Транспорт
        transport_items = [
            ("Газель", "gazelle", "1.5 т"),
            ("Грузовик ЗИЛ", "truck", "5 т"),
            ("Легковой автомобиль", "car", "500 кг"),
            ("Фургон", "van", "1 т"),
            ("Спецтехника", "special", "до 10 т")
        ]
        for name, typ, cap in transport_items:
            await db.execute('''INSERT INTO transport (name, type, capacity, is_available)
                VALUES (?, ?, ?, ?)''', (name, typ, cap, 1))
        # Заказы
        work_types = ["🚚 Доставка", "🛠 Демонтаж", "📦 Переезд", "♻️ Вывоз мусора", "🪑 Сборка мебели"]
        addresses = ["Gedimino pr. 9", "Didžioji g. 15", "Pilies g. 7", "Konstitucijos pr. 20", "Laisvės pr. 60"]
        statuses = ["pending", "assigned", "in_progress", "completed"]
        for i in range(50):
            user_id = random.randint(1000, 9999)
            username = f"client_{random.randint(1,100)}"
            work_type = random.choice(work_types)
            days = random.randint(0,30)
            scheduled_date = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
            scheduled_time = f"{random.randint(8,20)}:00"
            address = random.choice(addresses)
            comment = f"Тестовый комментарий {i}" if random.random()>0.5 else ""
            status = random.choice(statuses)
            cost = random.randint(50, 400)
            await db.execute('''INSERT INTO orders (user_id, username, work_type, scheduled_date, scheduled_time, address, comment, status, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, username, work_type, scheduled_date, scheduled_time, address, comment, status, cost))
        await db.commit()
        print("✅ Тестовые данные добавлены")

if __name__ == "__main__":
    asyncio.run(generate())
