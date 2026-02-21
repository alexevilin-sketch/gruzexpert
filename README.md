# GRUZEXPERT Telegram Bot

Бот для расчета стоимости грузоперевозок и создания заказов.

## Деплой на Hyperlift

### 1. Подготовка
1. Создайте репозиторий на GitHub
2. Загрузите все файлы бота
3. Уберите токен из кода (он уже убран в переменную окружения)

### 2. Настройка в Starlight Hyperlift Manager
1. Подключите ваш GitHub репозиторий
2. Укажите путь к Dockerfile
3. Добавьте переменные окружения:
   - `BOT_TOKEN=8573711643:AAFceOUgqdnNFr_Wct2TPegImJSpGA-OwNQ`
4. Запустите сборку

### 3. Установка webhook
После деплоя выполните:
```python
import requests
TOKEN = "ваш_токен"
WEBHOOK_URL = "https://ваш-домен.hyperlift.app/webhook"
requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
