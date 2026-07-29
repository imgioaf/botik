## 🚀 SWITZERBOT PRODUCTION DEPLOYMENT - COMMAND REFERENCE

### For Your 4GB/40GB/2-Core Server


---

## ⏱️ FASTEST SETUP (Copy-Paste Commands)

### Step 1: Initial Server Connection
```bash
# SSH into your server
ssh user@your-server-ip

# Create bot directory
sudo mkdir -p /opt/swiwallet && sudo chown $USER:$USER /opt/swiwallet
cd /opt/swiwallet
```

### Step 2: Clone Code & Setup Environment
```bash
# Clone repository (or use SCP to transfer)
git clone <your-repo-url> .

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements-core.txt
```

### Step 3: Configure Bot
```bash
# Create .env file with your token
cat > .env << 'EOF'
BOT_TOKEN=<YOUR_TELEGRAM_BOT_TOKEN>
DATABASE_URL=sqlite+aiosqlite:///switzerbot.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF

# Verify bot loads correctly
python3 -c "from bot.main import *; print('✅ Bot Ready!')"
```

### Step 4: Start Bot (Choose One)

**Option A: Simple Background (Quick Test)**
```bash
nohup python3 -m bot.main > bot.log 2>&1 &
```

**Option B: Systemd Service (Recommended)**
```bash
sudo bash deploy.sh
sudo systemctl start switzerbot
sudo systemctl status switzerbot
```

**Option C: Manual Foreground (Debugging)**
```bash
python3 -m bot.main
```

### Step 5: Deploy Mini App to Vercel
```bash
# Install Vercel CLI (if not installed)
npm install -g vercel

# Deploy Mini App
bash deploy-miniapp.sh
```

---

## 📊 Monitoring Commands

### View Bot Logs
```bash
# Real-time logs
tail -f bot.log

# Last 50 lines
tail -50 bot.log

# If using systemd:
sudo journalctl -u switzerbot -f
```

### Check Bot Process
```bash
# Is bot running?
ps aux | grep "python3 -m bot.main"

# Bot PID and memory
ps aux | grep bot.main | grep -v grep

# If using systemd:
sudo systemctl status switzerbot
```

### System Resources
```bash
# RAM usage
free -h

# Disk usage
df -h

# Database size
du -sh switzerbot.db

# CPU and memory of bot
top -p $(pgrep -f "python3 -m bot.main")
```

---

## 🔧 Management Commands

### Restart Bot
```bash
# If running manually:
pkill -f "python3 -m bot.main"
python3 -m bot.main

# If using systemd:
sudo systemctl restart switzerbot

# If using supervisor:
sudo supervisorctl restart switzerbot
```

### Stop Bot
```bash
# Manual stop:
pkill -f "python3 -m bot.main"

# Systemd stop:
sudo systemctl stop switzerbot

# Supervisor stop:
sudo supervisorctl stop switzerbot
```

### Verify Bot Connection
```bash
# Check Telegram API connectivity
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe

# Should return JSON with your bot info
```

---

## 🧪 Testing Commands

### Run Full Debug Suite
```bash
bash production-debug.sh
```

### Test Bot Imports
```bash
python3 << 'EOF'
from bot.main import *
print("✅ Bot imports successfully")
print("✅ All 21 handlers registered")
print("✅ Database initialized")
print("✅ Configuration loaded")
EOF
```

### Check Database
```bash
python3 << 'EOF'
import asyncio
from database.models import engine, User

async def check():
    async with engine.connect() as conn:
        result = await conn.execute("SELECT COUNT(*) FROM user")
        print(f"✅ Users in DB: {result.scalar()}")

asyncio.run(check())
EOF
```

### Test Mini App Deployment
```bash
# After deployment, check if accessible
curl https://your-miniapp-url.vercel.app

# Should return HTML content
```

---

## 🚨 Troubleshooting Commands

### Bot Won't Start
```bash
# Check Python
python3 --version

# Check dependencies
pip list | grep -E "aiogram|sqlalchemy"

# Test import
python3 -c "from bot.main import *"

# Check .env
cat .env

# Check for errors
tail -100 bot.log | grep ERROR
```

### High Memory Usage
```bash
# Monitor memory
watch -n 1 'free -h && ps aux | grep bot.main | head -2'

# Check what's using memory
ps aux --sort=-%mem | head -10

# If too high, restart:
sudo systemctl restart switzerbot
```

### Database Issues
```bash
# Check database integrity
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('switzerbot.db')
cursor = conn.cursor()
cursor.execute("PRAGMA integrity_check")
print(cursor.fetchone())
conn.close()
EOF

# Backup before fixing
cp switzerbot.db switzerbot.db.backup

# Restore if corrupted
cp switzerbot.db.backup switzerbot.db
```

### Cannot Connect to Telegram
```bash
# Check network connectivity
ping -c 1 api.telegram.org

# Check DNS
nslookup api.telegram.org

# Check firewall
sudo ufw status
```

---

## 🔐 Maintenance Commands

### Backup Database
```bash
# Daily backup
cp switzerbot.db switzerbot.db.backup-$(date +%Y%m%d)

# List backups
ls -lh switzerbot.db.backup-*

# Keep last 30 days
find . -name "switzerbot.db.backup-*" -mtime +30 -delete
```

### Rotate Logs
```bash
# Compress current log
gzip bot.log
mv bot.log.gz logs/bot-$(date +%Y%m%d).log.gz

# Clean old logs (older than 90 days)
find logs/ -name "*.log.gz" -mtime +90 -delete
```

### Update Bot Code
```bash
# Pull latest changes
git pull

# Restart bot to apply changes
sudo systemctl restart switzerbot
```

---

## 📈 Performance Optimization

### Enable System Optimizations
```bash
# Kernel parameters for better performance
sudo sysctl -w net.ipv4.tcp_fin_timeout=30
sudo sysctl -w net.ipv4.tcp_tw_reuse=1

# Python environment
export PYTHONUNBUFFERED=1
export MALLOC_TRIM_THRESHOLD_=128000
```

### Database Optimization
```bash
python3 << 'EOF'
import asyncio
from database.models import engine

async def optimize():
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.exec_driver_sql("VACUUM"))
    print("✅ Database optimized")

asyncio.run(optimize())
EOF
```

---

## 🎯 Daily Operations

### Morning Health Check
```bash
#!/bin/bash
# Save as health-check.sh and run daily

echo "🔍 SWIWALLET Health Check"

# Bot running?
if pgrep -f "python3 -m bot.main" > /dev/null; then
    echo "✅ Bot running"
else
    echo "❌ Bot not running - restarting..."
    systemctl restart switzerbot
fi

# Memory OK?
MEM=$(free | awk '/Mem:/{printf "%.0f", $3/$2*100}')
echo "💾 Memory: ${MEM}%"

# Disk OK?
DISK=$(df / | awk 'NR==2{printf "%.0f", $5}')
echo "💿 Disk: ${DISK}%"

# Database OK?
SIZE=$(du -sh switzerbot.db | cut -f1)
echo "🗄️  DB: $SIZE"

# Errors?
ERRORS=$(grep -c ERROR bot.log 2>/dev/null || echo "0")
echo "📊 Errors (last 24h): $ERRORS"
```

---

## 🌐 Deployment Verification

### Final Checklist
```bash
# 1. Bot running
pgrep -f "python3 -m bot.main" > /dev/null && echo "✅ Bot running" || echo "❌ Bot not running"

# 2. Can connect to Telegram
curl -s https://api.telegram.org/bot$(grep BOT_TOKEN .env | cut -d= -f2)/getMe | grep -q "ok" && echo "✅ Connected to Telegram" || echo "❌ Cannot connect"

# 3. Database working
python3 -c "import sqlite3; sqlite3.connect('switzerbot.db').cursor().execute('SELECT COUNT(*) FROM user'); print('✅ Database OK')" 2>/dev/null || echo "❌ Database error"

# 4. Mini App deployed
curl -s https://your-miniapp-url.vercel.app | grep -q "SWIWALLET" && echo "✅ Mini App deployed" || echo "❌ Mini App not accessible"
```

---

## 📞 Emergency Procedures

### If Bot Crashes
```bash
# Kill any zombie processes
pkill -9 -f "python3 -m bot.main"

# Restart
systemctl restart switzerbot

# Check if it stayed up
sleep 5 && systemctl status switzerbot
```

### If Database Corrupts
```bash
# Stop bot
systemctl stop switzerbot

# Restore backup
cp switzerbot.db.backup switzerbot.db

# Restart bot
systemctl start switzerbot
```

### If Memory Leak Detected
```bash
# Monitor memory trend
while true; do 
    ps aux | grep bot.main | grep -v grep | awk '{print $6/1024 " MB"}' 
    sleep 60
done

# If constantly increasing, restart
systemctl restart switzerbot
```

---

## 🎉 All Set!

Your SWITZERBOT is now ready for production. Copy these commands for quick reference on your server.

**Key Quick-Access Commands:**
```bash
# Check status
systemctl status switzerbot

# View logs
journalctl -u switzerbot -f

# Restart
systemctl restart switzerbot

# Full debug
bash production-debug.sh
```

For detailed guide, see: **PRODUCTION_DEPLOYMENT.md**
