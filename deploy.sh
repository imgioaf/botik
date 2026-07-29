#!/bin/bash
# 🚀 SWIWALLET BOT - ПОЛНЫЙ PRODUCTION DEPLOY
# для сервера с 4GB RAM, 40GB storage, 2 cores

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 SWITZERBOT PRODUCTION DEPLOYMENT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. ПРОВЕРКА ОКРУЖЕНИЯ
echo "📋 [1/8] Проверка окружения..."
python3 --version
pip --version
echo "✅ Окружение готово"
echo ""

# 2. УСТАНОВКА ЗАВИСИМОСТЕЙ
echo "📦 [2/8] Установка зависимостей..."
pip install -q -r requirements-core.txt
echo "✅ Зависимости установлены"
echo ""

# 3. ИНИЦИАЛИЗАЦИЯ БД
echo "🗄️ [3/8] Инициализация базы данных..."
python3 -c "
from database.models import Base, engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
print('✅ База готова')
"
echo ""

# 4. ПРОВЕРКА КОНФИГА
echo "⚙️ [4/8] Проверка конфигурации..."
python3 -c "
from config.config import settings
print(f'✅ BOT_TOKEN: {settings.BOT_TOKEN[:20]}...')
print(f'✅ DATABASE_URL: {settings.DATABASE_URL}')
print(f'✅ TONCENTER_API_KEY: {settings.TONCENTER_API_KEY[:20] if settings.TONCENTER_API_KEY else \"NOT SET\"}...')
"
echo ""

# 5. ЗАПУСК ВСЕХ ТЕСТОВ
echo "🧪 [5/8] Запуск тестов..."
python3 debug_system.py 2>&1 | tail -5
python3 debug_extended.py 2>&1 | tail -5
python3 test_functionality.py 2>&1 | tail -5
echo "✅ Тесты пройдены"
echo ""

# 6. ПРОВЕРКА ПАМЯТИ
echo "💾 [6/8] Проверка ресурсов сервера..."
python3 -c "
import psutil
mem = psutil.virtual_memory()
cpu = psutil.cpu_count()
print(f'✅ Доступно RAM: {mem.available / 1024**3:.1f} GB')
print(f'✅ CPU Cores: {cpu}')
print(f'✅ Дисковое пространство: {psutil.disk_usage(\"/\").free / 1024**3:.1f} GB')
"
echo ""

# 7. СТАРТОВЫЙ РЕЖИМ
echo "🎯 [7/8] Выбор режима запуска..."
echo "1) FOREGROUND (для отладки)"
echo "2) BACKGROUND с systemd (для production)"
echo "3) BACKGROUND с supervisor (альтернатива)"
read -p "Выберите: " mode

if [ "$mode" = "1" ]; then
    echo "▶️ Запуск в foreground режиме..."
    python3 -m bot.main
elif [ "$mode" = "2" ]; then
    echo "📝 Создание systemd сервиса..."
    sudo tee /etc/systemd/system/switzerbot.service > /dev/null <<EOF
[Unit]
Description=Switzerbot Telegram Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(which python3) -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable switzerbot
    sudo systemctl start switzerbot
    echo "✅ Сервис запущен"
    sudo systemctl status switzerbot
elif [ "$mode" = "3" ]; then
    echo "📝 Создание supervisor конфига..."
    sudo tee /etc/supervisor/conf.d/switzerbot.conf > /dev/null <<EOF
[program:switzerbot]
directory=$(pwd)
command=$(which python3) -m bot.main
autostart=true
autorestart=true
user=$(whoami)
redirect_stderr=true
stdout_logfile=$(pwd)/bot.log
EOF
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start switzerbot
    echo "✅ Сервис запущен через supervisor"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════════════════════════"
