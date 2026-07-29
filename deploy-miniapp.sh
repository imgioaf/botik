#!/bin/bash
# 🚀 MINI APP DEPLOYMENT TO VERCEL
# Deploy blockchain/index.html as Telegram Mini App

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  📱 SWIWALLET MINI APP - VERCEL DEPLOYMENT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. CHECK VERCEL CLI
echo "🔍 [1/5] Проверка Vercel CLI..."
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI не найден"
    echo "📥 Установка: npm install -g vercel"
    npm install -g vercel
fi
echo "✅ Vercel CLI готов"
echo ""

# 2. CREATE VERCEL PROJECT STRUCTURE
echo "📁 [2/5] Создание структуры проекта..."
mkdir -p .vercel-deploy
cp blockchain/index.html .vercel-deploy/index.html

# Create vercel.json
cat > .vercel-deploy/vercel.json << 'EOF'
{
  "buildCommand": "echo 'Mini App - no build needed'",
  "outputDirectory": ".",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=3600, s-maxage=3600"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "SAMEORIGIN"
        }
      ]
    }
  ]
}
EOF

# Create package.json
cat > .vercel-deploy/package.json << 'EOF'
{
  "name": "swiwallet-miniapp",
  "version": "2.5.1",
  "description": "SWIWALLET Alpine Web3 Ecosystem Mini App",
  "private": true,
  "engines": {
    "node": "20.x"
  }
}
EOF

echo "✅ Структура готова"
echo ""

# 3. TELEGRAM MINI APP CONFIGURATION
echo "⚙️  [3/5] Конфигурация Mini App..."

cat > .vercel-deploy/telegram-config.json << 'EOF'
{
  "app_name": "SWIWALLET",
  "short_name": "SWI",
  "version": "2.5.1",
  "description": "Alpine Web3 Ecosystem",
  "start_url": "/",
  "display": "fullscreen",
  "orientation": "portrait-primary",
  "background_color": "#0a0d14",
  "theme_color": "#0a0d14",
  "scope": "/",
  "screenshots": [
    {
      "src": "https://images.unsplash.com/photo-1549880338-65ddcdfd017b",
      "sizes": "540x720",
      "type": "image/jpeg",
      "form_factor": "narrow"
    }
  ]
}
EOF

echo "✅ Mini App конфигурирована"
echo ""

# 4. DEPLOY TO VERCEL
echo "🚀 [4/5] Развертывание на Vercel..."
cd .vercel-deploy

# Attempt login if not already authenticated
if [ ! -f ~/.vercel/auth.json ]; then
    echo "📝 Требуется вход в Vercel"
    vercel login
fi

# Deploy
DEPLOYMENT=$(vercel --prod --token=$VERCEL_TOKEN 2>&1 || vercel --prod)
MINI_APP_URL=$(echo "$DEPLOYMENT" | grep -oP 'https://[^\s]+' | head -1)

if [ -z "$MINI_APP_URL" ]; then
    MINI_APP_URL="swiwallet.vercel.app"
fi

echo "✅ Развернуто на: $MINI_APP_URL"
cd ..
echo ""

# 5. UPDATE BOT CONFIGURATION
echo "📝 [5/5] Обновление конфигурации бота..."

# Update miniapp handler with correct URL
cat > ../bot/handlers/miniapp_update.py << EOF
# AUTO-GENERATED: Mini App URL configuration
MINIAPP_URL = "$MINI_APP_URL"

# Mini App Actions Mapping
MINIAPP_ACTIONS = {
    'launch': '/start',
    'wallet': '/wallet',
    'assets': '/wallet',
    'split': '/split_payment',
    'legacy': '/legacy',
    'tournaments': '/tournaments'
}
EOF

echo "✅ Конфигурация обновлена"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  ✅ MINI APP SUCCESSFULLY DEPLOYED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Deployment Summary:"
echo "  🌐 URL: $MINI_APP_URL"
echo "  📱 Telegram: https://t.me/switzerbot?startapp=miniapp"
echo "  🔧 Framework: Tailwind CSS + Vanilla JS"
echo "  ✨ Features: Telegram WebApp API, Dark Theme, Responsive"
echo ""
echo "🔗 Integration:"
echo "  In bot config, set: MINIAPP_URL = '$MINI_APP_URL'"
echo ""
echo "📋 Next step:"
echo "  1. Test Mini App: /miniapp in @switzerbot"
echo "  2. Monitor: Check Vercel dashboard"
echo "  3. Update: Push changes to trigger auto-deploy"
echo ""
