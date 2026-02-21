#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -f "cargo.db" ]; then
    echo -e "${RED}❌ База данных не найдена${NC}"
    exit 1
fi

echo -e "${BLUE}${BOLD}════════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}     📊 СТАТИСТИКА РАСЧЕТОВ GRUZEXPERT     ${NC}"
echo -e "${BLUE}${BOLD}════════════════════════════════════════════${NC}"
echo ""

# Python скрипт для статистики
python3 << EOF
import sqlite3
from datetime import datetime, timedelta

try:
    conn = sqlite3.connect('cargo.db')
    c = conn.cursor()
    
    # Общее количество
    c.execute("SELECT COUNT(*) FROM calculations")
    total = c.fetchone()[0]
    print(f"📊 Всего расчетов: {total}")
    
    # За сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM calculations WHERE date(created_at) = ?", (today,))
    today_count = c.fetchone()[0]
    print(f"📅 За сегодня: {today_count}")
    
    # За неделю
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM calculations WHERE date(created_at) >= ?", (week_ago,))
    week_count = c.fetchone()[0]
    print(f"📆 За неделю: {week_count}")
    
    # Общая сумма
    c.execute("SELECT SUM(total_cost) FROM calculations")
    total_sum = c.fetchone()[0] or 0
    print(f"💰 Общая сумма: {total_sum:.0f} €")
    
    # Средний чек
    if total > 0:
        avg = total_sum / total
        print(f"💳 Средний чек: {avg:.0f} €")
    
    # Последние 5 расчетов
    print("\n🕒 Последние расчеты:")
    c.execute("""
        SELECT id, total_cost, datetime(created_at, 'localtime') 
        FROM calculations 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    for row in c.fetchall():
        print(f"   #{row[0]}: {row[1]} € ({row[2]})")
    
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")
