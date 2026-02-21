#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

# Функция для вывода логотипа
show_logo() {
    echo -e "${GREEN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              🚚 GRUZEXPERT - ТЕРМИНАЛ                     ║"
    echo "║              ТЕЛЕГРАМ БОТ КАЛЬКУЛЯТОР v2.0                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_logo

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден${NC}"
    exit 1
fi

# Показываем версию Python
PY_VERSION=$(python3 --version)
echo -e "${BLUE}🔍 Найден: $PY_VERSION${NC}"

# Виртуальное окружение
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Создание виртуального окружения...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}📦 Установка зависимостей...${NC}"
    pip install --upgrade pip
    pip install aiogram==3.4.1 aiosqlite==0.19.0 aiohttp==3.9.1 python-dotenv==1.0.0
    
    # Проверка установки
    echo -e "${YELLOW}🔍 Проверка установки...${NC}"
    python3 -c "import aiogram; print('✅ aiogram установлен')" || {
        echo -e "${RED}❌ Ошибка установки aiogram${NC}"
        exit 1
    }
else
    source venv/bin/activate
    echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"
    
    # Проверка наличия aiogram в окружении
    python3 -c "import aiogram" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  aiogram не найден в окружении. Устанавливаю...${NC}"
        pip install aiogram==3.4.1 aiosqlite==0.19.0 aiohttp==3.9.1 python-dotenv==1.0.0
    }
fi

# Проверка наличия файла с токеном
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден${NC}"
    echo -e "${BLUE}Создаю шаблон .env файла...${NC}"
    cat > .env << 'EOF'
# Токен бота (получить у @BotFather)
BOT_TOKEN=8573711643:AAFceOUgqdnNFr_Wct2TPegImJSpGA-OwNQ

# Настройки email для отправки расчетов (опционально)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
TARGET_EMAIL=orders@gruzexpert.info
EOF
    echo -e "${GREEN}✅ Шаблон .env создан${NC}"
    echo -e "${YELLOW}⚠️  Отредактируйте файл .env и добавьте свои данные!${NC}"
    echo -e "${YELLOW}   nano .env${NC}"
    
    # Ждем подтверждения от пользователя
    read -p "Нажмите Enter после редактирования .env файла или Ctrl+C для выхода..."
fi

# Загрузка переменных из .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Проверка токена
if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}❌ BOT_TOKEN не установлен в .env файле${NC}"
    exit 1
fi

# Остановка старых процессов
echo -e "${YELLOW}⏹️  Остановка старых процессов...${NC}"
pkill -f "python.*bot.py" 2>/dev/null
if [ -f "bot.pid" ]; then
    OLD_PID=$(cat bot.pid 2>/dev/null)
    kill -9 $OLD_PID 2>/dev/null
    rm -f bot.pid
fi
sleep 2

# Проверка наличия базы данных
if [ ! -f "cargo.db" ]; then
    echo -e "${YELLOW}📁 База данных не найдена. Будет создана при первом запуске.${NC}"
fi

# Создание директории для логов
mkdir -p logs
LOG_FILE="logs/bot_$(date +%Y%m%d_%H%M%S).log"

# Запуск бота
echo -e "${YELLOW}🤖 Запуск Telegram бота...${NC}"
echo -e "${BLUE}📝 Лог-файл: $LOG_FILE${NC}"

# Запуск бота
python3 bot.py > "$LOG_FILE" 2>&1 &
BOT_PID=$!
echo $BOT_PID > bot.pid
sleep 3

# Проверка запуска
if kill -0 $BOT_PID 2>/dev/null; then
    echo -e "${GREEN}✅ БОТ УСПЕШНО ЗАПУЩЕН [PID: $BOT_PID]${NC}"
    
    # Получаем информацию о боте через Telegram API
    BOT_INFO=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe")
    if [[ $BOT_INFO == *"\"ok\":true"* ]]; then
        BOT_USERNAME=$(echo $BOT_INFO | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}   @$BOT_USERNAME${NC}"
    fi
else
    echo -e "${RED}❌ ОШИБКА ЗАПУСКА БОТА${NC}"
    echo -e "${YELLOW}Последние строки лога:${NC}"
    tail -n 10 "$LOG_FILE"
    exit 1
fi

# Функция проверки статуса
check_status() {
    if kill -0 $BOT_PID 2>/dev/null; then
        CPU=$(ps -p $BOT_PID -o %cpu | tail -1 | tr -d ' ' 2>/dev/null || echo "N/A")
        MEM=$(ps -p $BOT_PID -o %mem | tail -1 | tr -d ' ' 2>/dev/null || echo "N/A")
        echo -e "${GREEN}   CPU: $CPU% | RAM: $MEM%${NC}"
        return 0
    else
        return 1
    fi
}

# Мониторинг в реальном времени
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}           ✅ СИСТЕМА ЗАПУЩЕНА                              ${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "📊 ${BOLD}СТАТУС:${NC}"
check_status

echo ""
echo -e "🤖 ${BOLD}БОТ:${NC}"
echo -e "   📝 Лог-файл:    ${GREEN}$LOG_FILE${NC}"
echo -e "   📁 База данных: ${GREEN}cargo.db${NC}"
echo -e "   📧 Email для расчетов: ${GREEN}$TARGET_EMAIL${NC}"

echo ""
echo -e "📋 ${BOLD}КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ:${NC}"
echo -e "   ${YELLOW}▶️  Просмотр лога:${NC} tail -f $LOG_FILE"
echo -e "   ${YELLOW}▶️  Остановка бота:${NC} ./stop.sh"
echo -e "   ${YELLOW}▶️  Перезапуск:${NC} ./restart.sh"

echo ""
echo -e "${GREEN}${BOLD}✅ Готово! Бот запущен и работает.${NC}"
