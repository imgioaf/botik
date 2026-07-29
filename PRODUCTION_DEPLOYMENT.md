# 🚀 SWIWALLET PRODUCTION DEPLOYMENT GUIDE

**Version**: 2.5.1  
**Target**: 4GB RAM, 40GB Storage, 2 CPU cores Linux server  
**Status**: ✅ PRODUCTION READY

---

## 📋 TABLE OF CONTENTS

1. [Server Setup](#server-setup)
2. [Bot Deployment](#bot-deployment)
3. [Mini App Deployment](#mini-app-deployment)
4. [Monitoring & Maintenance](#monitoring--maintenance)
5. [Troubleshooting](#troubleshooting)

---

## 🖥️ SERVER SETUP

### Step 1: Initial Server Configuration

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11+
sudo apt-get install -y python3.11 python3.11-venv python3-pip
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev

# Create bot directory
sudo mkdir -p /opt/swiwallet
sudo chown $USER:$USER /opt/swiwallet
cd /opt/swiwallet

# Clone or transfer bot code
# If using git: git clone <repo> .
# If transferring: scp -r ./* user@server:/opt/swiwallet/
```

### Step 2: Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements-core.txt

# Verify installation
python3 -c "from bot.main import *; print('✅ Bot imports OK')"
```

### Step 3: Environment Configuration

```bash
# Create .env file
cat > .env << 'EOF'
BOT_TOKEN=<your-bot-token-here>
DATABASE_URL=sqlite+aiosqlite:///switzerbot.db
REDIS_URL=redis://localhost:6379/0
TONCENTER_API_KEY=<optional-ton-api-key>
TON_MASTER_MNEMONIC=<optional-ton-wallet-mnemonic>
LOG_LEVEL=INFO
WEBHOOK_URL=https://yourdomain.com/webhook  # For webhook mode
EOF

# Secure .env
chmod 600 .env
```

---

## 🤖 BOT DEPLOYMENT

### Option 1: Long Polling (Recommended for simple setup)

```bash
# Run production debug first
bash production-debug.sh

# Start bot (foreground for testing)
python3 -m bot.main

# Or start in background
nohup python3 -m bot.main > bot.log 2>&1 &
```

### Option 2: Systemd Service (Recommended for production)

```bash
# Create service file
sudo tee /etc/systemd/system/switzerbot.service > /dev/null << 'EOF'
[Unit]
Description=SWIWALLET Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/swiwallet
Environment="PATH=/opt/swiwallet/venv/bin"
ExecStart=/opt/swiwallet/venv/bin/python3 -m bot.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable switzerbot
sudo systemctl start switzerbot

# Check status
sudo systemctl status switzerbot
sudo journalctl -u switzerbot -f  # View logs
```

### Option 3: Supervisor (Alternative)

```bash
# Install supervisor
sudo apt-get install -y supervisor

# Create config
sudo tee /etc/supervisor/conf.d/switzerbot.conf > /dev/null << 'EOF'
[program:switzerbot]
directory=/opt/swiwallet
command=/opt/swiwallet/venv/bin/python3 -m bot.main
autostart=true
autorestart=true
user=ubuntu
redirect_stderr=true
stdout_logfile=/opt/swiwallet/bot.log
EOF

# Apply and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start switzerbot
```

---

## 📱 MINI APP DEPLOYMENT

### Step 1: Deploy to Vercel

```bash
# Install Vercel CLI (if not already installed)
npm install -g vercel

# Run deployment script
bash deploy-miniapp.sh

# Or manual deployment
cd blockchain
vercel --prod
```

### Step 2: Configure Bot for Mini App

```python
# In bot/handlers/miniapp.py, update:
MINIAPP_URL = "https://your-miniapp.vercel.app"  # Get from deploy output

# Test Mini App
# Send /miniapp command to bot from Telegram
```

### Step 3: Verify Deployment

- Open bot in Telegram
- Send `/miniapp` command
- Click "Launch SWIWALLET"
- Verify all 6 action buttons work:
  - ✅ Deposit
  - ✅ Withdraw
  - ✅ Transfer
  - ✅ History
  - ✅ 2FA
  - ✅ Devices

---

## 📊 MONITORING & MAINTENANCE

### Real-time Monitoring

```bash
# View bot logs
tail -f bot.log

# System resources
watch -n 1 'ps aux | grep python3 | grep -v grep'
free -h && df -h

# Database size
du -sh switzerbot.db

# Telegram connection status
# Enable debug logging in config
LOG_LEVEL=DEBUG python3 -m bot.main
```

### Health Check Script

```bash
#!/bin/bash
# save as health-check.sh

echo "📊 SWIWALLET Health Check"
echo "=========================="

# Check bot process
if pgrep -f "python3 -m bot.main" > /dev/null; then
    echo "✅ Bot running"
else
    echo "❌ Bot not running"
    systemctl restart switzerbot
fi

# Check database
python3 << 'EOF'
import os
if os.path.exists('switzerbot.db'):
    size = os.path.getsize('switzerbot.db') / 1024 / 1024
    print(f"✅ Database: {size:.1f} MB")
EOF

# Check system resources
MEM=$(free | awk '/Mem:/{printf "%.1f%%", $3/$2*100}')
CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{printf "%.0f%%", 100-$1}')
echo "💾 Memory: $MEM"
echo "⚙️  CPU: $CPU"

# Check recent errors
if tail -20 bot.log | grep -q "ERROR"; then
    echo "⚠️  Recent errors found:"
    tail -5 bot.log | grep ERROR
else
    echo "✅ No recent errors"
fi
```

### Daily Maintenance

```bash
# Backup database
cp switzerbot.db switzerbot.db.backup-$(date +%Y%m%d)

# Rotate logs
gzip bot.log
mv bot.log.gz logs/bot-$(date +%Y%m%d).log.gz

# Cleanup old files
find . -name "*.log.gz" -mtime +30 -delete
```

---

## 🔧 TROUBLESHOOTING

### Bot not starting

```bash
# Check Python
python3 --version

# Check imports
python3 -c "from bot.main import *"

# Check .env
cat .env

# Check logs
tail -50 bot.log
```

### Database errors

```bash
# Check database integrity
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('switzerbot.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())
conn.close()
EOF

# Restore from backup if corrupted
cp switzerbot.db.backup switzerbot.db
```

### Mini App not loading

1. Check Vercel deployment status
2. Verify `MINIAPP_URL` in bot configuration
3. Clear browser cache
4. Test on different device

### High memory usage

```bash
# Check process memory
ps aux | grep python3

# Monitor in real-time
top -p $(pgrep -f "python3 -m bot.main")

# If too high, may need to restart
systemctl restart switzerbot
```

### Database locked

```bash
# Find process holding lock
lsof switzerbot.db

# Restart bot if needed
systemctl restart switzerbot
```

---

## 📈 PERFORMANCE OPTIMIZATION

### For 4GB RAM Server

```bash
# Kernel parameters (optimal for bot)
sudo sysctl -w net.ipv4.tcp_fin_timeout=30
sudo sysctl -w net.ipv4.tcp_tw_reuse=1

# Python environment
export PYTHONUNBUFFERED=1
export MALLOC_TRIM_THRESHOLD_=128000
```

### Database Optimization

```python
# Periodic maintenance
import asyncio
from database.models import engine

async def optimize():
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: conn.exec_driver_sql("VACUUM"))
        
asyncio.run(optimize())
```

---

## 🔐 SECURITY CHECKLIST

- [ ] `.env` file has correct permissions (chmod 600)
- [ ] BOT_TOKEN is secure and not committed to git
- [ ] HTTPS/TLS enabled for webhook (if using webhooks)
- [ ] Database backup strategy in place
- [ ] Regular security updates applied
- [ ] Logs monitored for suspicious activity
- [ ] Rate limiting active on bot handlers
- [ ] 2FA enabled for admin accounts

---

## 📞 SUPPORT & CONTACT

- **Bot**: @switzerbot
- **Telegram Channel**: @swiwallet
- **Emergency**: Restart bot with `systemctl restart switzerbot`

---

**Last Updated**: 2025-01-01  
**Deployment Status**: ✅ READY FOR PRODUCTION
