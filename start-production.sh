#!/bin/bash
# 🎯 SWIWALLET BOT - PRODUCTION STARTUP
# Optimal configuration for 4GB RAM, 40GB storage, 2 cores

set -e

APP_NAME="SWITZERBOT"
APP_VERSION="2.5.1"
LOG_FILE="bot.log"
PID_FILE=".bot.pid"

echo "════════════════════════════════════════════════════════════════"
echo "  🎬 $APP_NAME PRODUCTION STARTUP v$APP_VERSION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. ENVIRONMENT CHECK
echo "🔍 Pre-flight checks..."
python3 -c "
import sys
import os
print(f'  ✅ Python: {sys.version.split()[0]}')
print(f'  ✅ CWD: {os.getcwd()}')
"

if [ ! -f "requirements-core.txt" ]; then
    echo "  ❌ requirements-core.txt не найден"
    exit 1
fi
echo "  ✅ Requirements file found"

if [ ! -f ".env" ]; then
    echo "  ⚠️  .env file not found - using defaults"
fi

echo ""

# 2. DEPENDENCY CHECK
echo "📦 Checking dependencies..."
python3 << 'PYEOF'
import sys
deps = ['aiogram', 'sqlalchemy', 'aiosqlite', 'pydantic_settings']
for dep in deps:
    try:
        __import__(dep)
        print(f"  ✅ {dep}")
    except ImportError:
        print(f"  ❌ {dep} missing - installing...")
        sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "  📥 Installing dependencies..."
    pip install -q -r requirements-core.txt
fi
echo ""

# 3. DATABASE INIT
echo "🗄️  Initializing database..."
python3 << 'PYEOF'
import asyncio
from database.models import Base, engine
import os

async def init_db():
    if not os.path.exists('switzerbot.db'):
        print("  📝 Creating database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✅ Database ready")

asyncio.run(init_db())
PYEOF
echo ""

# 4. MEMORY OPTIMIZATION
echo "⚙️  Applying performance optimizations..."
export PYTHONUNBUFFERED=1
export MALLOC_TRIM_THRESHOLD_=128000
export MALLOC_MMAP_THRESHOLD_=131072

python3 << 'PYEOF'
import gc
gc.set_debug(0)
print("  ✅ Memory optimization applied")
PYEOF
echo ""

# 5. STARTUP
echo "🚀 Starting bot..."
echo ""

# Create startup wrapper
cat > _bot_runner.py << 'PYEOF'
#!/usr/bin/env python3
import sys
import asyncio
import signal
import logging
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("=" * 60)
        logger.info("🎬 SWITZERBOT STARTUP")
        logger.info("=" * 60)
        
        from bot.main import main as bot_main
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("⏹️  Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
PYEOF

# Run bot with graceful shutdown
python3 _bot_runner.py &
BOT_PID=$!
echo $BOT_PID > $PID_FILE

# Signal handlers
trap 'kill $BOT_PID 2>/dev/null; rm -f $PID_FILE' EXIT TERM INT

echo "📊 Bot started with PID: $BOT_PID"
echo "📋 Logs: tail -f bot.log"
echo "⏹️  Stop: kill $BOT_PID"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ BOT IS RUNNING"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Wait for process
wait $BOT_PID
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Bot stopped cleanly"
else
    echo "❌ Bot crashed with code $EXIT_CODE"
fi

exit $EXIT_CODE
