#!/bin/bash
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    echo -e "${GREEN}🛑 Останавливаем бота (PID: $PID)...${NC}"
    kill -9 $PID 2>/dev/null
    rm bot.pid
    echo -e "${GREEN}✅ Бот остановлен${NC}"
else
    echo -e "${RED}❌ Бот не запущен${NC}"
fi
