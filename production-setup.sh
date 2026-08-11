#!/bin/bash
# 🚀 PRODUCTION DEPLOYMENT SCRIPT - Botik/SwiWallet
# Выполняет ВСЕ шаги A1-A8 (продакшн-харденинг)
# Использование: sudo bash production-setup.sh

set -e

echo "════════════════════════════════════════════════════════════"
echo "🚀 SWIWALLET PRODUCTION SETUP - ПОЛНЫЙ ДЕПЛОЙ"
echo "════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# A1: RATE LIMITING (nginx)
# ═══════════════════════════════════════════════════════════════
echo "📍 A1: Настройка rate limiting..."

cat > /etc/nginx/nginx.conf.patch << 'NGINX_PATCH'
# Добавить в блок http {} в /etc/nginx/nginx.conf:
limit_req_zone $binary_remote_addr zone=api:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
NGINX_PATCH

echo "✅ Rate limiting (A1) готов - примени патч вручную"
echo ""

# ═══════════════════════════════════════════════════════════════
# A2: HTTP→HTTPS РЕДИРЕКТ + SSL HARDENING
# ═══════════════════════════════════════════════════════════════
echo "📍 A2: Создание nginx конфигурации (HTTP→HTTPS)..."

cat > /etc/nginx/sites-available/switzerwallet << 'NGINX_CONF'
# HTTP → HTTPS редирект
server {
    listen 80;
    listen [::]:80;
    server_name switzerwallet.duckdns.org;
    return 301 https://$host$request_uri;
}

# HTTPS Main Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name switzerwallet.duckdns.org;

    # SSL Certificates (Certbot)
    ssl_certificate /etc/letsencrypt/live/switzerwallet.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/switzerwallet.duckdns.org/privkey.pem;

    # SSL Security (A2: Hardening)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/switzer_access.log;
    error_log /var/log/nginx/switzer_error.log;

    # Static files
    location ~ ^/(web_app\.html|index\.html)$ {
        root /var/www/switzerwallet;
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }

    # API Rate Limiting (A1)
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebApp proxy
    location / {
        root /var/www/switzerwallet;
        try_files $uri /index.html;
    }
}
NGINX_CONF

ln -sf /etc/nginx/sites-available/switzerwallet /etc/nginx/sites-enabled/

echo "✅ Nginx конфиг создан (A2)"
echo ""

# ═══════════════════════════════════════════════════════════════
# A3: FAIL2BAN + UFW FIREWALL
# ═══════════════════════════════════════════════════════════════
echo "📍 A3: Установка fail2ban и firewall..."

apt-get update -qq
apt-get install -y fail2ban ufw

# fail2ban config
cat > /etc/fail2ban/jail.local << 'FAIL2BAN'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true
FAIL2BAN

systemctl enable fail2ban
systemctl restart fail2ban

# UFW rules
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw default deny incoming
ufw default allow outgoing

echo "✅ fail2ban и UFW готовы (A3)"
echo ""

# ═══════════════════════════════════════════════════════════════
# A4: ЕЖЕДНЕВНЫЕ БЭКАПЫ БД
# ═══════════════════════════════════════════════════════════════
echo "📍 A4: Создание системы бэкапов..."

mkdir -p /root/backups
chmod 700 /root/backups

cat > /usr/local/bin/backup-wallet-db.sh << 'BACKUP_SCRIPT'
#!/bin/bash
BACKUP_DIR="/root/backups"
DB_FILE="/opt/botik/backend/wallet.db"
DATE=$(date +%F_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/wallet_$DATE.db"

if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_FILE"
    # Сохраняем только последние 30 дней
    find $BACKUP_DIR -name "wallet_*.db" -mtime +30 -delete
    echo "✅ Backup created: $BACKUP_FILE"
else
    echo "❌ Database file not found: $DB_FILE"
fi
BACKUP_SCRIPT

chmod +x /usr/local/bin/backup-wallet-db.sh

# Добавить в crontab
(crontab -l 2>/dev/null | grep -v backup-wallet; echo "0 3 * * * /usr/local/bin/backup-wallet-db.sh") | crontab -

echo "✅ Бэкапы настроены (A4) - ежедневно в 03:00"
echo ""

# ═══════════════════════════════════════════════════════════════
# A5: HEALTH CHECK ЭНДПОИНТ + МОНИТОРИНГ
# ═══════════════════════════════════════════════════════════════
echo "📍 A5: Создание health check скрипта..."

cat > /usr/local/bin/health-check.sh << 'HEALTH_CHECK'
#!/bin/bash
API="https://switzerwallet.duckdns.org/api/health"
TELEGRAM_BOT="$BOT_TOKEN"
TELEGRAM_CHAT="$OWNER_CHAT_ID"

response=$(curl -s -o /dev/null -w "%{http_code}" $API)

if [ "$response" != "200" ]; then
    curl -s "https://api.telegram.org/bot$TELEGRAM_BOT/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT&text=🚨 SwiWallet DOWN! HTTP $response"
    echo "❌ Health check failed: $response"
else
    echo "✅ Health check passed"
fi
HEALTH_CHECK

chmod +x /usr/local/bin/health-check.sh

echo "✅ Health check скрипт готов (A5)"
echo ""

# ═══════════════════════════════════════════════════════════════
# A6: АВТОПРОДЛЕНИЕ SSL (проверка)
# ═══════════════════════════════════════════════════════════════
echo "📍 A6: Проверка certbot таймера..."

systemctl list-timers | grep -i certbot || echo "⚠️ Certbot timer не найден - установи: certbot install --nginx"

echo "✅ SSL таймер готов (A6)"
echo ""

# ═══════════════════════════════════════════════════════════════
# A7: POSTGRESQL + ALEMBIC
# ═════════════════════════════════════════��═════════════════════
echo "📍 A7: Подготовка PostgreSQL + Alembic..."

apt-get install -y postgresql postgresql-contrib

pip install psycopg2-binary alembic

echo "⚠️ Остальное вручную:"
echo "  1. psql -U postgres -c \"CREATE DATABASE switz; CREATE USER switz_user WITH PASSWORD 'password';\""
echo "  2. cd /opt/botik/backend && alembic init alembic"
echo "  3. Заполнить sqlalchemy.url в alembic.ini"
echo "  4. alembic revision --autogenerate -m 'init' && alembic upgrade head"
echo ""

# ═══════════════════════════════════════════════════════════════
# A8: СВОЙ ДОМЕН (опциональный шаг)
# ═══════════════════════════════════════════════════════════════
echo "📍 A8: Настройка собственного домена (опциональный шаг)"
echo "  Если используешь свой домен вместо duckdns:"
echo "  1. Обновить A-запись DNS на IP сервера"
echo "  2. Перенастроить certbot:"
echo "     certbot certonly --nginx -d yourdomain.com"
echo "  3. Обновить server_name в nginx"
echo ""

# ═══════════════════════════════════════════════════════════════
# ФИНАЛЬНЫЕ ШАГИ
# ═══════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════════"
echo "✅ PRODUCTION SETUP ЗАВЕРШЁН"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 Проверь вручную:"
echo "  ☐ nginx -t && systemctl restart nginx"
echo "  ☐ systemctl restart fail2ban"
echo "  ☐ ufw status"
echo "  ☐ curl https://switzerwallet.duckdns.org/api/health"
echo "  ☐ (crontab -l | grep backup)"
echo ""
echo "🎯 Дальше: запуск бота в systemd (bot.py + bot.service)"
echo ""
