#!/bin/bash
# 🎯 SWITZERBOT - ONE-COMMAND PRODUCTION DEPLOYMENT
# Для вашего сервера с 4GB RAM, 40GB Storage, 2 CPU cores

# ════════════════════════════════════════════════════════════════════════════
# COMPLETE DEPLOYMENT IN ONE COMMAND SUITE
# ════════════════════════════════════════════════════════════════════════════

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║           🚀 SWITZERBOT PRODUCTION DEPLOYMENT - AUTO SETUP 🚀             ║"
echo "║                                                                            ║"
echo "║        Target: 4GB RAM | 40GB Storage | 2 CPU Cores Linux Server          ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# PHASE 1: PRE-FLIGHT CHECKS
# ════════════════════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1/5: PRE-FLIGHT CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check OS
if [[ ! "$OSTYPE" == "linux-gnu"* ]]; then
    echo "⚠️  Warning: This script is optimized for Linux (detected: $OSTYPE)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as non-root (for security)
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Warning: Running as root is not recommended. Consider using sudo instead."
   read -p "Continue? (y/n) " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    sudo apt-get update && sudo apt-get install -y python3.11 python3-pip python3-venv
fi
echo "✅ Python $(python3 --version | cut -d' ' -f2) found"

# Check git (optional)
if ! command -v git &> /dev/null; then
    echo "⚠️  Git not found (needed for deployment from repository)"
    echo "   Install with: sudo apt-get install -y git"
fi

# Check available disk space
DISK_FREE=$(df / | awk 'NR==2 {print $4}')
if [ "$DISK_FREE" -lt 1000000 ]; then
    echo "❌ Less than 1GB disk space available!"
    exit 1
fi
echo "✅ Disk space: OK ($(( DISK_FREE / 1024 / 1024 ))GB available)"

echo ""

# ════════════════════════════════════════════════════════════════════════════
# PHASE 2: ENVIRONMENT SETUP
# ════════════════════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2/5: ENVIRONMENT SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create bot directory
BOT_DIR="/opt/swiwallet"
if [ -d "$BOT_DIR" ]; then
    echo "⚠️  Directory $BOT_DIR already exists"
    read -p "Use existing directory? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting"
        exit 1
    fi
else
    echo "📁 Creating directory: $BOT_DIR"
    sudo mkdir -p "$BOT_DIR"
    sudo chown $USER:$USER "$BOT_DIR"
fi

cd "$BOT_DIR"
echo "✅ Working directory: $BOT_DIR"

# Clone or verify code
if [ ! -f "bot/main.py" ]; then
    echo "📥 Bot code not found. Please transfer code first:"
    echo ""
    echo "   Option 1: From GitHub"
    echo "   git clone <repo> ."
    echo ""
    echo "   Option 2: From local machine"
    echo "   scp -r c:\\switzerbot/* user@server:/opt/swiwallet/"
    echo ""
    exit 1
fi
echo "✅ Bot code verified"

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "✅ Virtual environment activated"

echo ""

# ════════════════════════════════════════════════════════════════════════════
# PHASE 3: DEPENDENCY INSTALLATION
# ════════════════════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3/5: DEPENDENCY INSTALLATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip setuptools wheel
pip install -q -r requirements-core.txt

echo "✅ Dependencies installed:"
python3 -c "
import sys
deps = ['aiogram', 'sqlalchemy', 'aiosqlite', 'cryptography', 'pyotp', 'qrcode']
for dep in deps:
    try:
        mod = __import__(dep)
        ver = getattr(mod, '__version__', 'installed')
        print(f'   ✅ {dep:<20} {ver}')
    except ImportError:
        print(f'   ❌ {dep:<20} FAILED')
        sys.exit(1)
"

echo ""

# ════════════════════════════════════════════════════════════════════════════
# PHASE 4: CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4/5: CONFIGURATION SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    echo ""
    read -p "Enter your Telegram BOT_TOKEN: " BOT_TOKEN
    
    cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
DATABASE_URL=sqlite+aiosqlite:///switzerbot.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF
    
    chmod 600 .env
    echo "✅ .env file created (permissions: 600)"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 << 'PYEOF'
import asyncio
from database.models import Base, engine

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")

asyncio.run(init())
PYEOF

# Test bot imports
echo "🤖 Testing bot import..."
python3 -c "from bot.main import *; print('✅ Bot imports successfully')"

echo ""

# ════════════════════════════════════════════════════════════════════════════
# PHASE 5: SERVICE SETUP & STARTUP
# ════════════════════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 5/5: SERVICE SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Choose deployment method:"
echo "1) Systemd (Recommended for production)"
echo "2) Manual background (Quick start)"
echo "3) Foreground (For debugging)"
read -p "Select (1-3): " MODE

case $MODE in
    1)
        echo "🔧 Setting up systemd service..."
        sudo tee /etc/systemd/system/switzerbot.service > /dev/null << EOF
[Unit]
Description=SWIWALLET Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python3 -m bot.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable switzerbot
        sudo systemctl start switzerbot
        
        echo "✅ Service enabled and started"
        echo "   Check status: sudo systemctl status switzerbot"
        echo "   View logs: sudo journalctl -u switzerbot -f"
        ;;
    2)
        echo "🚀 Starting bot in background..."
        nohup python3 -m bot.main > bot.log 2>&1 &
        BOT_PID=$!
        echo "✅ Bot started with PID: $BOT_PID"
        echo "   View logs: tail -f bot.log"
        ;;
    3)
        echo "🚀 Starting bot in foreground (Ctrl+C to stop)..."
        python3 -m bot.main
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Summary:"
echo "  Location: $BOT_DIR"
echo "  Python: $(python3 --version)"
echo "  Packages: $(pip list | grep -c '^')"
echo ""
echo "📱 Next Steps:"
echo "  1. Test bot: Open Telegram and find @switzerbot"
echo "  2. Send /start command"
echo "  3. Test Mini App: Send /miniapp"
echo ""
echo "📖 Documentation:"
echo "  • Full guide: $BOT_DIR/PRODUCTION_DEPLOYMENT.md"
echo "  • Commands: $BOT_DIR/COMMAND_REFERENCE.md"
echo "  • Troubleshoot: See PRODUCTION_DEPLOYMENT.md section 5"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
