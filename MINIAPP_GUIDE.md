# 🚀 Telegram Mini App Integration Guide

## What is a Mini App?
A Mini App is an interactive web application embedded directly inside Telegram. It runs inside a WebView window and can communicate with your bot.

## How It Works
1. **User clicks a button** with `WebAppInfo` → Opens Mini App
2. **Mini App opens** in WebView → Can show custom interface
3. **User interacts** with Mini App → Sends data back to bot
4. **Bot receives** the data → Processes and updates user state

## Implementation in Switzerbot

### Step 1: Create Mini App HTML File

Create `web_app.html` (already exists in your project):

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Switzerbot Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        button {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
        button:active {
            opacity: 0.7;
        }
        .info {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 Switzerbot Mini App</h1>
        
        <div class="info">
            <h3>Quick Actions</h3>
            <button onclick="sendData('deposit')">💵 Deposit</button>
            <button onclick="sendData('withdraw')">📤 Withdraw</button>
            <button onclick="sendData('transfer')">↔️ Transfer</button>
            <button onclick="sendData('history')">📊 History</button>
        </div>
        
        <div class="info">
            <h3>Settings</h3>
            <button onclick="sendData('2fa')">🔐 2FA Settings</button>
            <button onclick="sendData('devices')">📱 Trusted Devices</button>
        </div>
        
        <div id="status" class="info" style="display:none;">
            <p id="statusText"></p>
        </div>
    </div>

    <script>
        // Initialize Telegram Mini App
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();

        // Send data back to bot
        function sendData(action) {
            const data = {
                action: action,
                timestamp: new Date().toISOString(),
                user_id: tg.initDataUnsafe?.user?.id
            };
            
            tg.sendData(JSON.stringify(data));
            
            showStatus(`✅ Sent: ${action}`);
        }

        function showStatus(message) {
            const status = document.getElementById('status');
            status.style.display = 'block';
            document.getElementById('statusText').textContent = message;
        }

        // Optional: Handle main button
        tg.MainButton.text = 'Complete Action';
        tg.MainButton.show();
        tg.MainButton.onClick(() => {
            tg.close();
        });

        // Optional: Change header color
        tg.setHeaderColor('#FFFFFF');
        tg.setBackgroundColor('#F5F5F5');
    </script>
</body>
</html>
```

### Step 2: Add Mini App Handler to Your Bot

Create a new file: `bot/handlers/miniapp.py`

```python
from aiogram import Router, types, F
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import json
import logging

logger = logging.getLogger(__name__)
router = Router()

# Configuration
MINIAPP_URL = "https://your-domain.com/web_app.html"  # Change this to your domain

@router.message(Command("miniapp"))
async def cmd_miniapp(message: types.Message):
    """Start Mini App"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🚀 Open Mini App",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]])
    
    await message.answer(
        "🎮 <b>Open Mini App for quick actions:</b>\n\n"
        "• 💰 Deposit crypto\n"
        "• 📤 Withdraw funds\n"
        "• ↔️ Send transfers\n"
        "• 🔐 Security settings",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.message(F.web_app_data)
async def handle_miniapp_data(message: types.Message):
    """Handle data from Mini App"""
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        user_id = data.get("user_id")
        
        logger.info(f"Mini App action: {action} from user {user_id}")
        
        if action == "deposit":
            await message.answer("💵 Deposit started...", parse_mode="HTML")
            # Handle deposit logic
            
        elif action == "withdraw":
            await message.answer("📤 Withdraw started...", parse_mode="HTML")
            # Handle withdraw logic
            
        elif action == "transfer":
            await message.answer("↔️ Transfer started...", parse_mode="HTML")
            # Handle transfer logic
            
        elif action == "history":
            await message.answer("📊 Transaction history...", parse_mode="HTML")
            # Handle history logic
            
        elif action == "2fa":
            await message.answer("🔐 2FA Settings...", parse_mode="HTML")
            # Handle 2FA logic
            
        elif action == "devices":
            await message.answer("📱 Trusted Devices...", parse_mode="HTML")
            # Handle devices logic
        
    except Exception as e:
        logger.error(f"Error handling mini app data: {e}")
        await message.answer("❌ Error processing request")
```

### Step 3: Register Mini App Router in Main Bot

Edit `bot/main.py`:

```python
from bot.handlers import miniapp  # Add this import

# Then in setup_routers():
dp.include_router(miniapp.router)
```

### Step 4: Host the Mini App

You need to host `web_app.html` on a public HTTPS server. Options:

#### Option A: Use Vercel (Free, Easiest)
1. Create GitHub account
2. Push `web_app.html` to repo
3. Deploy on Vercel (automatic)
4. Get URL like `https://yourapp.vercel.app/web_app.html`

#### Option B: Use Your Own Server
```bash
# Using Python Flask
pip install flask
```

Create `app.py`:
```python
from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/web_app.html')
def web_app():
    return send_file('web_app.html', mimetype='text/html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

Then use reverse proxy (nginx) with SSL for HTTPS.

#### Option C: Use PythonAnywhere (Easy)
1. Upload files to pythonanywhere.com
2. Get free HTTPS domain
3. Use URL in Mini App

### Step 5: Update Your Main Menu

Add Mini App button to main menu in `bot/handlers/menu.py`:

```python
def get_main_inline_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Mini App", web_app=WebAppInfo(url=MINIAPP_URL))
    kb.button(text="💰 Wallet", callback_data="wallet_main")
    # ... rest of buttons
    return kb.as_markup()
```

### Step 6: Test It

1. Send `/miniapp` to your bot
2. Click "🚀 Open Mini App"
3. Button should open web interface
4. Click actions → data goes back to bot

## Security Notes ⚠️

```python
# ALWAYS validate data from Mini App:

@router.message(F.web_app_data)
async def handle_miniapp_data(message: types.Message, session: AsyncSession):
    """Safely handle Mini App data"""
    
    # 1. Verify user is authenticated
    user = await get_or_create_user(session, message.from_user.id)
    if not user.is_verified:
        await message.answer("❌ Please verify first")
        return
    
    # 2. Validate data structure
    try:
        data = json.loads(message.web_app_data.data)
        assert isinstance(data, dict)
        assert 'action' in data
    except:
        await message.answer("❌ Invalid data format")
        return
    
    # 3. Sanitize inputs
    action = str(data['action']).lower()
    if not action.isalnum():
        await message.answer("❌ Invalid action")
        return
    
    # 4. Rate limit
    # Check if user sent too many requests
    
    # 5. Log actions
    logger.info(f"User {user.id} triggered action: {action}")
```

## Advanced Features

### Send Messages from Mini App
```javascript
// In Mini App JavaScript
tg.sendData(JSON.stringify({
    action: 'send_message',
    text: 'Hello from Mini App!'
}));
```

### Get User Data in Mini App
```javascript
const initData = tg.initDataUnsafe;
console.log('User:', initData.user);
console.log('User ID:', initData.user.id);
console.log('Username:', initData.user.username);
```

### Change Theme Based on User Preference
```javascript
const tg = window.Telegram.WebApp;

if (tg.colorScheme === 'dark') {
    document.body.style.backgroundColor = '#1e1e1e';
    document.body.style.color = '#ffffff';
} else {
    document.body.style.backgroundColor = '#ffffff';
    document.body.style.color = '#000000';
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Mini App won't open | Check MINIAPP_URL is HTTPS and accessible |
| Data not reaching bot | Verify `F.web_app_data` filter and handler registration |
| WebView shows blank | Check browser console for JS errors |
| Telegram.WebApp not defined | Ensure script tag `<script src="https://telegram.org/js/telegram-web-app.js"></script>` is present |

## Next Steps

1. **Deploy Mini App** to HTTPS server
2. **Update MINIAPP_URL** in your code
3. **Test thoroughly** before production
4. **Add payment integration** (BotFather Payments)
5. **Monitor usage** with analytics

That's it! Your Mini App is ready! 🎉
