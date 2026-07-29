# 🚀 SwiWallet - Complete Deployment Guide

**Target**: Ubuntu Server (95.182.91.220)  
**App**: Next.js + Telegram Mini App + Landing Page  
**Domain**: swiwallet.com (your actual domain)

---

## 📋 Pre-Deployment Checklist

- [ ] Telegram Bot Token obtained from @BotFather
- [ ] Domain name purchased and DNS configured
- [ ] Server SSH access verified
- [ ] Node.js 18+ installed on local machine
- [ ] All code tested locally

---

## 🔑 Step 1: Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/start`
3. Send `/newbot` to create new bot
4. Choose bot name (e.g., "SwiWallet") and username (e.g., "swiwallet_bot")
5. **Save the token** (looks like: `123456789:ABCDEFghij...`)

---

## 📨 Step 2: Configure Environment

### Local Setup

```bash
# Navigate to project
cd swiwallet-app

# Copy environment template
cp .env.example .env.local

# Edit .env.local
nano .env.local
```

Add your values:
```env
TELEGRAM_BOT_TOKEN=your_token_from_botfather
NEXT_PUBLIC_API_URL=https://swiwallet.com
NEXT_PUBLIC_MINI_APP_URL=https://swiwallet.com/app
NODE_ENV=development
```

### Test Locally

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Visit http://localhost:3000
```

---

## 🔧 Step 3: Prepare Server

### SSH Access

```bash
# Test connection
ssh root@95.182.91.220

# You should see the server prompt
```

### Update System

```bash
ssh root@95.182.91.220 << 'EOF'
apt-get update
apt-get upgrade -y
apt-get install -y build-essential curl git wget
EOF
```

### Install Node.js

```bash
ssh root@95.182.91.220 << 'EOF'
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt-get install -y nodejs
node --version
npm --version
EOF
```

### Install PM2 (Process Manager)

```bash
ssh root@95.182.91.220 << 'EOF'
npm install -g pm2
pm2 --version
EOF
```

---

## 📦 Step 4: Deploy Application

### Option A: Automated Deployment (Recommended ✅)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment (from PowerShell on Windows)
bash deploy.sh
```

### Option B: Manual Deployment (Step by Step)

#### 1. Create app directory on server

```bash
ssh root@95.182.91.220 << 'EOF'
mkdir -p /opt/swiwallet
cd /opt/swiwallet
EOF
```

#### 2. Upload files via rsync

```bash
# From Windows PowerShell:
rsync -avz --delete `
  --exclude node_modules `
  --exclude .git `
  --exclude .next `
  --exclude .env.local `
  ./ root@95.182.91.220:/opt/swiwallet/
```

#### 3. Install dependencies on server

```bash
ssh root@95.182.91.220 << 'EOF'
cd /opt/swiwallet
npm install --production
npm run build
EOF
```

#### 4. Create environment file on server

```bash
ssh root@95.182.91.220 << 'EOF'
cat > /opt/swiwallet/.env.production << 'ENVEOF'
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://swiwallet.com
TELEGRAM_BOT_TOKEN=your_bot_token_here
NEXT_PUBLIC_MINI_APP_URL=https://swiwallet.com/app
ENVEOF

chmod 600 /opt/swiwallet/.env.production
EOF
```

#### 5. Start application with PM2

```bash
ssh root@95.182.91.220 << 'EOF'
cd /opt/swiwallet
pm2 start npm --name "swiwallet" -- start
pm2 startup
pm2 save
pm2 logs swiwallet --lines 20
EOF
```

---

## 🔐 Step 5: Setup HTTPS (SSL Certificate)

### Install Certbot

```bash
ssh root@95.182.91.220 << 'EOF'
apt-get install -y certbot python3-certbot-nginx
EOF
```

### Get SSL Certificate

```bash
ssh root@95.182.91.220 << 'EOF'
certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --agree-tos \
  -m admin@your-domain.com \
  --non-interactive
EOF
```

---

## 🌐 Step 6: Setup Nginx Reverse Proxy

### Install Nginx

```bash
ssh root@95.182.91.220 << 'EOF'
apt-get install -y nginx
EOF
```

### Create Nginx Configuration

```bash
ssh root@95.182.91.220 << 'EOF'
cat > /etc/nginx/sites-available/ksey-bank << 'NGINX'
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/javascript;
    gzip_min_length 1000;

    # Proxy to Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90;
    }

    # Cache static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

# Enable site
ln -sf /etc/nginx/sites-available/ksey-bank /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
systemctl enable nginx
EOF
```

---

## 📱 Step 7: Configure Telegram Bot

### Set Webhook (Optional - for webhook mode)

```bash
# Get your URL
WEBHOOK_URL="https://your-domain.com/api/telegram/webhook"

# Set webhook via Telegram API
curl -X POST "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}"
```

### Set Mini App URL

1. Open @BotFather
2. Send `/mybots`
3. Select your bot
4. Select "Bot Settings"
5. Select "Menu button"
6. "Configure menu button"
7. Enter Mini App URL: `https://your-domain.com/app`

Or via API:

```bash
curl -X POST "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setChatMenuButton" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_button": {
      "type": "web_app",
      "text": "Open Ksey Bank",
      "web_app": {
        "url": "https://your-domain.com/app"
      }
    }
  }'
```

---

## ✅ Step 8: Verify Deployment

### Check if app is running

```bash
ssh root@95.182.91.220 << 'EOF'
pm2 status
pm2 logs ksey-bank --lines 20
EOF
```

### Test HTTPS

```bash
# Test domain
curl -I https://your-domain.com

# Should return 200 OK
```

### Test Mini App

1. Open Telegram
2. Find your bot (@your-bot-username)
3. Tap "Menu" button
4. Tap "Open Ksey Bank"
5. Mini App should load

### Check Performance

```bash
ssh root@95.182.91.220 << 'EOF'
# Memory usage
pm2 monit

# Server stats
free -h
df -h
EOF
```

---

## 🔄 Updating the Application

### After making code changes:

```bash
# Rebuild locally
npm run build

# Deploy (option 1 - automated)
./deploy.sh

# Deploy (option 2 - manual)
rsync -avz --delete \
  --exclude node_modules \
  --exclude .git \
  --exclude .next \
  ./ root@95.182.91.220:/opt/ksey-bank/

# Restart on server
ssh root@95.182.91.220 'cd /opt/ksey-bank && npm run build && pm2 restart ksey-bank'
```

---

## 🐛 Troubleshooting

### App not loading

```bash
# Check logs
ssh root@95.182.91.220 'pm2 logs ksey-bank'

# Check if running
ssh root@95.182.91.220 'pm2 status'

# Restart
ssh root@95.182.91.220 'pm2 restart ksey-bank'
```

### HTTPS certificate issues

```bash
# Renew certificate
ssh root@95.182.91.220 'certbot renew'

# Check certificate
ssh root@95.182.91.220 'certbot certificates'
```

### Nginx issues

```bash
# Check Nginx status
ssh root@95.182.91.220 'systemctl status nginx'

# View Nginx error log
ssh root@95.182.91.220 'tail -f /var/log/nginx/error.log'

# Test Nginx config
ssh root@95.182.91.220 'nginx -t'
```

### Port already in use

```bash
# Find process using port 3000
ssh root@95.182.91.220 'lsof -i :3000'

# Kill process if needed
ssh root@95.182.91.220 'kill -9 <PID>'

# Restart PM2
ssh root@95.182.91.220 'pm2 restart ksey-bank'
```

---

## 📊 Monitoring

### Daily Health Check

```bash
ssh root@95.182.91.220 << 'EOF'
echo "=== PM2 Status ==="
pm2 status

echo "=== Memory Usage ==="
free -h

echo "=== Disk Usage ==="
df -h

echo "=== Nginx Status ==="
systemctl status nginx

echo "=== Recent Logs ==="
pm2 logs ksey-bank --lines 10
EOF
```

### Auto-restart on reboot

```bash
ssh root@95.182.91.220 << 'EOF'
pm2 startup
pm2 save
EOF
```

---

## 🎉 Success!

Your Ksey Bank application is now live!

### Access Points

- 🌐 Landing Page: `https://your-domain.com`
- 📱 Mini App: `https://your-domain.com/app`
- 🤖 Telegram Bot: `https://t.me/your-bot-username`

### Support

- Documentation: See README.md
- Telegram: @kseybot
- Channel: @kseychannel

---

**Deployment Date**: $(date)  
**Version**: 1.0.0  
**Status**: ✅ LIVE
