"""
SWITZERBOT - QUICK START GUIDE
===============================

## Prerequisites
- Python 3.10+
- Virtual environment (recommended)
- TON Wallet with funds for testing
- TON Center API key (free at https://toncenter.com)

## Installation

1. Create virtual environment:
   python -m venv venv

2. Activate virtual environment:
   # Windows:
   venv\Scripts\Activate
   
   # macOS/Linux:
   source venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

## Configuration

1. Copy .env.example to .env:
   cp .env.example .env

2. Edit .env with your values:
   - BOT_TOKEN: Get from @BotFather on Telegram
   - DATABASE_URL: sqlite+aiosqlite:///./switzerbot.db (for testing)
   - TONCENTER_API_KEY: Get from https://toncenter.com
   - TON_MASTER_MNEMONIC: Your 24-word seed phrase

   ⚠️  NEVER commit .env to git!
   ⚠️  KEEP MNEMONIC SECRET - it controls ALL user wallets!

## Running the Bot

Start the bot:
   python -m bot.main

Expected output:
   2026-05-29 12:00:00 [INFO] asyncio_tasks: Creating task pool
   2026-05-29 12:00:01 [INFO] ton_monitor: TON deposit monitor started
   2026-05-29 12:00:02 [INFO] bot.main: ✅ Bot @Switzerwalletbot started

The bot will now:
- Listen for Telegram messages
- Monitor TON deposits every 15 seconds
- Process transfers, withdrawals, and other commands

## Testing Commands in Telegram

Start bot: /start
View wallet: /wallet
Make transfer: /transfer @username 10 USDT
Withdraw: /withdraw TON EQxxx... 5
View referrals: /referral
Settings: /settings

## Database

SQLite (development):
- File: switzerbot.db (auto-created)
- No additional setup needed

PostgreSQL (production):
- Update DATABASE_URL in .env:
  DATABASE_URL=postgresql+asyncpg://user:password@localhost/switzerbot
- Create database:
  psql -U postgres -c "CREATE DATABASE switzerbot;"

## Troubleshooting

### ModuleNotFoundError: No module named 'aiogram'
→ Solution: Activate virtual environment and install requirements
   source venv/bin/activate  # or venv\Scripts\Activate on Windows
   pip install -r requirements.txt

### ValidationError: Field required [BOT_TOKEN]
→ Solution: Create .env file with all required settings
   cp .env.example .env
   # Edit .env with your values

### TON deposit not detected
→ Check:
  1. TON_MASTER_MNEMONIC is correct (24 words)
  2. TONCENTER_API_KEY is valid
  3. Deposit address is from /wallet command
  4. Transaction is on TON mainnet (not testnet)
  5. Check logs for API errors

### Database locked (SQLite)
→ Solution: Close other connections or switch to PostgreSQL for production

## Security

✅ All transfers use database locks (prevents double-spending)
✅ Rate limiting enabled (5 req/sec per user)
✅ Audit logging for all financial operations
✅ Error handling with automatic rollback
✅ Exponential backoff for blockchain operations

⚠️  DO NOT:
  - Share .env file or mnemonic
  - Run multiple bot instances with same wallet (wallet locking issues)
  - Set very high transfer limits without KYC
  - Use testnet mnemonic on mainnet (and vice versa)

## Monitoring

Check logs:
   tail -f switzerbot.log  # or view in console during running

Key metrics to monitor:
  - TON deposit confirmation time (should be < 60 seconds)
  - Transfer success rate (should be > 99%)
  - Withdrawal confirmation time (depends on network)
  - Error rate (aim for < 0.1%)

## Deployment

For production, recommended:
  1. Use PostgreSQL instead of SQLite
  2. Set up systemd service or Docker
  3. Enable HSM/KMS for key management
  4. Set up monitoring (Prometheus, Grafana)
  5. Configure backups and disaster recovery
  6. Use separate .env files per environment
  7. Enable SSL certificates for all connections

Example systemd service:
   [Unit]
   Description=Switzerbot Telegram Wallet
   After=network.target

   [Service]
   Type=simple
   User=switzerbot
   WorkingDirectory=/opt/switzerbot
   Environment=\"PATH=/opt/switzerbot/venv/bin\"
   ExecStart=/opt/switzerbot/venv/bin/python -m bot.main
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target

## Support

For issues:
1. Check SECURITY_AUDIT_REPORT.md for architecture details
2. Enable debug logging: logging.basicConfig(level=logging.DEBUG)
3. Check TON Center API status: https://toncenter.com/status
4. Review error logs for specific error messages

---
Last updated: 2026-05-29
Version: 1.0
"""
