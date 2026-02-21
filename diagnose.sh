#!/bin/bash

echo "🔍 ДИАГНОСТИКА СИСТЕМЫ"
echo "======================"

echo -e "\n📦 Python packages:"
pip list | grep -E "flask|aiogram|aiosqlite"

echo -e "\n📁 Файлы проекта:"
ls -la bot.py website.py templates/ 2>/dev/null

echo -e "\n🗄️ База данных:"
sqlite3 cargo.db ".tables" 2>/dev/null || echo "❌ БД не найдена"

echo -e "\n🌐 Порт 5000:"
sudo lsof -i :5000 2>/dev/null || echo "✅ Порт свободен"

echo -e "\n📄 Лог сайта (последние 10 строк):"
tail -n 10 website.log 2>/dev/null || echo "❌ Лог не найден"

echo -e "\n📄 Лог бота (последние 10 строк):"
tail -n 10 bot.log 2>/dev/null || echo "❌ Лог не найден"
