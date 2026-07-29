# SwiWallet - Telegram Mini App & Landing Page

Beautiful Dark Glassmorphism UI with Liquid Metal for Telegram Crypto Wallet.

## Features

- 🎨 **Dark Glassmorphism Design** - Premium UI with glass effect
- 🌊 **Liquid Metal Background** - Animated metallic gradient
- 📱 **Telegram Mini App** - Full integration with Telegram WebApp API
- 💳 **Wallet Management** - Deposit, Withdraw, Transfer
- 🔒 **Security Features** - 2FA, Device Whitelist
- 📊 **Transaction History** - View all transactions
- 🌐 **Landing Page** - Marketing site with FAQ
- ⚡ **Next.js** - Fast, optimized, production-ready

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Telegram Bot Token

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/swiwallet.git
cd swiwallet

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your Telegram Bot Token
# TELEGRAM_BOT_TOKEN=your_token_here

# Run development server
npm run dev
```

Visit:
- Landing Page: http://localhost:3000
- Mini App: http://localhost:3000/app

## Project Structure

```
ksey-app/
├── src/
│   ├── app/
│   │   ├── page.tsx           # Landing page
│   │   ├── app/
│   │   │   └── page.tsx       # Mini App
│   │   ├── api/
│   │   │   ├── wallet/        # Wallet API
│   │   │   └── telegram/      # Telegram verification
│   │   ├── globals.css        # Global styles
│   │   └── layout.tsx         # Root layout
│   ├── components/            # Reusable components
│   └── lib/                   # Utilities
├── public/
│   └── assets/               # Images, videos
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Deployment

### Deploy to Ubuntu Server (95.182.91.220)

#### 1. SSH into Server

```bash
ssh root@95.182.91.220
```

#### 2. Install Node.js & PM2

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt-get install -y nodejs

# Install PM2
npm install -g pm2
```

#### 3. Clone & Setup Project

```bash
cd /opt
git clone https://github.com/yourusername/ksey-bank.git
cd ksey-bank

# Install dependencies
npm install

# Build for production
npm run build

# Create .env file
nano .env.local
# Add your environment variables
```

#### 4. Setup HTTPS with Certbot

```bash
# Install Certbot
apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Create Nginx config (see below)
```

#### 5. Setup Nginx Reverse Proxy

```bash
# Install Nginx
apt-get install -y nginx

# Create config
nano /etc/nginx/sites-available/ksey

# Add this config:
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/ksey /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### 6. Start Application with PM2

```bash
# Start
pm2 start npm --name "ksey-bank" -- start

# Monitor
pm2 monit

# Setup startup
pm2 startup
pm2 save
```

#### 7. Setup Telegram Mini App

In your Telegram Bot settings, set the Mini App URL to:
```
https://your-domain.com/app
```

## Environment Variables

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token

# Optional
NEXT_PUBLIC_API_URL=https://your-domain.com
BOT_API_URL=http://your-bot-backend:8000
NODE_ENV=production
```

## Scripts

```bash
npm run dev      # Development
npm run build    # Build for production
npm start        # Start production server
npm run lint     # Run linter
```

## Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS, Custom CSS
- **APIs**: Telegram WebApp API, REST
- **Hosting**: Ubuntu Server (Nginx, PM2)
- **Security**: HTTPS, Environment variables

## API Endpoints

### Wallet API
- `GET /api/wallet/balance` - Get wallet balance
- `POST /api/wallet/balance` - Update balance (deposit/withdraw)

### Telegram API
- `POST /api/telegram/verify` - Verify Telegram data

## Security Considerations

- ✅ HTTPS only (required for Telegram WebApp)
- ✅ Telegram signature verification
- ✅ Environment variables for secrets
- ✅ CORS configured
- ✅ Rate limiting recommended

## Troubleshooting

### App not loading
- Check Telegram Mini App URL is correct
- Verify HTTPS certificate
- Check browser console for errors

### API not responding
- Ensure BOT_API_URL is correct
- Check firewall rules
- Verify bot is running

### Build issues
- Delete `node_modules` and reinstall: `npm install`
- Clear Next.js cache: `rm -rf .next`
- Check Node.js version: `node --version`

## Support

- Telegram: @kseybot
- Channel: @kseychannel
- Email: support@kseybank.io

## License

MIT License - feel free to use for your projects

---

**Made with ❤️ for Telegram**
