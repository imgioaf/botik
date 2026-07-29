#!/bin/bash

# 🚀 SwiWallet - Automated Deployment to Ubuntu Server
# Deploy to: 95.182.91.220

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          🚀 SWIWALLET DEPLOYMENT AUTOMATION 🚀                ║"
echo "║                                                                ║"
echo "║            Deploy Telegram Mini App + Landing Page            ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
SERVER_IP="95.182.91.220"
SERVER_USER="root"
APP_DIR="/opt/swiwallet"
DOMAIN="swiwallet.com"  # Change to your domain
BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[1/8]${NC} Checking prerequisites..."

# Check if domain is set
if [ "$DOMAIN" == "ksey-bank.io" ]; then
  echo -e "${RED}Please set your domain in the script!${NC}"
  exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
  echo -e "${RED}Node.js not found. Installing...${NC}"
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
  apt-get install -y nodejs
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}\n"

echo -e "${YELLOW}[2/8]${NC} Building Next.js app..."
npm run build
echo -e "${GREEN}✓ Build complete${NC}\n"

echo -e "${YELLOW}[3/8]${NC} Connecting to server..."
ssh -o ConnectTimeout=10 ${SERVER_USER}@${SERVER_IP} "echo 'Connected'" || {
  echo -e "${RED}Cannot connect to server. Check IP and SSH access.${NC}"
  exit 1
}
echo -e "${GREEN}✓ Server connection OK${NC}\n"

echo -e "${YELLOW}[4/8]${NC} Uploading files to server..."
rsync -avz --delete \
  --exclude node_modules \
  --exclude .git \
  --exclude .next \
  --exclude .env.local \
  ./ ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/

echo -e "${GREEN}✓ Files uploaded${NC}\n"

echo -e "${YELLOW}[5/8]${NC} Installing dependencies on server..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/ksey-bank
npm install --production
ENDSSH
echo -e "${GREEN}✓ Dependencies installed${NC}\n"

echo -e "${YELLOW}[6/8]${NC} Setting up environment variables..."
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
cat > /opt/ksey-bank/.env.production << 'EOF'
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://${DOMAIN}
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
NEXT_PUBLIC_MINI_APP_URL=https://${DOMAIN}/app
EOF

chmod 600 /opt/ksey-bank/.env.production
ENDSSH
echo -e "${GREEN}✓ Environment configured${NC}\n"

echo -e "${YELLOW}[7/8]${NC} Starting application with PM2..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/ksey-bank

# Install PM2 if not already installed
npm install -g pm2

# Start application
pm2 start npm --name "swiwallet" -- start

# Setup startup
pm2 startup
pm2 save

# Display logs
pm2 logs swiwallet --lines 20
ENDSSH
echo -e "${GREEN}✓ Application started${NC}\n"

echo -e "${YELLOW}[8/8]${NC} Setting up HTTPS with Certbot..."
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
# Install Certbot if needed
apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot certonly --standalone -d swiwallet.com -d www.swiwallet.com --agree-tos -m admin@swiwallet.com --non-interactive || true

# Create Nginx config
mkdir -p /etc/nginx/sites-available

cat > /etc/nginx/sites-available/swiwallet << 'NGINX'
server {
    listen 80;
    server_name swiwallet.com www.swiwallet.com;
    return 301 https://$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name swiwallet.com www.swiwallet.com;

    ssl_certificate /etc/letsencrypt/live/swiwallet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/swiwallet.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 90;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

# Enable Nginx site
ln -sf /etc/nginx/sites-available/swiwallet /etc/nginx/sites-enabled/

# Test Nginx config
nginx -t

# Restart Nginx
systemctl restart nginx

# Setup auto-renewal
certbot renew --quiet --no-eff-email
ENDSSH

echo -e "${GREEN}✓ HTTPS configured${NC}\n"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║              ✅ DEPLOYMENT SUCCESSFUL! ✅                      ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Your SwiWallet app is now live!${NC}"
echo ""
echo "📍 Access points:"
echo "   Landing:  https://swiwallet.com"
echo "   Mini App: https://swiwallet.com/app"
echo ""
echo "📊 Server management:"
echo "   SSH:      ssh ${SERVER_USER}@${SERVER_IP}"
echo "   App dir:  ${APP_DIR}"
echo "   PM2:      ssh ${SERVER_USER}@${SERVER_IP} 'pm2 monit'"
echo "   Logs:     ssh ${SERVER_USER}@${SERVER_IP} 'pm2 logs swiwallet'"
echo ""
echo "🔧 To update in future:"
echo "   1. Make changes locally"
echo "   2. Run: ./deploy.sh"
echo ""
