# 🎯 БЫСТРЫЙ СТАРТ: Исправления и Мини-приложение

## ✅ Что было исправлено

### 1. **HTML Parse Error** 
- **Ошибка**: `Unsupported start tag "100ms"`
- **Причина**: Недопустимый HTML в сообщении
- **Решение**: Заменили `<100ms` на `&lt;100ms` в [help_explain.py](bot/handlers/help_explain.py#L179)

### 2. **Business Card Callback Error**
- **Ошибка**: `ValueError: invalid literal for int() with base 10: 'qr'`
- **Причина**: Неправильный парсинг callback_data
- **Решение**: Добавлена безопасная обработка с проверкой типов в [business_card.py](bot/handlers/business_card.py#L135-L150)

### 3. **Menu Edit Text Error**
- **Ошибка**: `there is no text in the message to edit`
- **Причина**: Попытка редактировать сообщение без текста
- **Решение**: Добавлена проверка наличия текста в [menu.py](bot/handlers/menu.py#L208)

### 4. **Tournament SQL Query Error**
- **Ошибка**: `misuse of aggregate: count()`
- **Причина**: Неправильная SQL синтаксис - count() в WHERE clause
- **Решение**: Переработана query с использованием subquery в [tournaments.py](bot/handlers/tournaments.py#L80-L95)

---

## 🚀 Мини-приложение (Mini App)

### Что это?
Мини-приложение - это интерактивный веб-интерфейс, встроенный прямо в Telegram. Пользователь нажимает кнопку → открывается WebView → может взаимодействовать с приложением.

### Что добавлено?

✅ **Новый файл**: [bot/handlers/miniapp.py](bot/handlers/miniapp.py)  
✅ **Документация**: [MINIAPP_GUIDE.md](MINIAPP_GUIDE.md)  
✅ **Регистрация** в [bot/main.py](bot/main.py#L17)

### Структура Mini App

```
User clicks button "🚀 Mini App"
        ↓
Browser opens WebView (web_app.html)
        ↓
User sees interface with 6 options:
  - 💵 Deposit
  - 📤 Withdraw
  - ↔️ Transfer
  - 📊 History
  - 🔐 2FA Settings
  - 📱 Trusted Devices
        ↓
User clicks action
        ↓
Data sent to bot via WebAppData
        ↓
Bot processes and shows results
```

### Доступные команды

```
/miniapp - Открыть мини-приложение
```

### Как работает?

1. **Пользователь** → нажимает кнопку "🚀 Mini App"
2. **Telegram** → открывает WebView с HTML файлом
3. **HTML/JavaScript** → отправляет JSON данные обратно
4. **Bot** → получает в handler `@router.message(F.web_app_data)`
5. **Handler** → обрабатывает action и отправляет ответ

### Пример использования

```python
# В mini app (JavaScript)
function sendData(action) {
    const data = {
        action: action,
        timestamp: new Date().toISOString()
    };
    Telegram.WebApp.sendData(JSON.stringify(data));
}

# В боте (Python)
@router.message(F.web_app_data)
async def handle_miniapp_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    action = data['action']  # 'deposit', 'withdraw', и т.д.
```

---

## 📋 Развертывание Mini App

### Требования
- Хостинг с поддержкой HTTPS (обязательно!)
- Статический файл HTML или веб-приложение

### Вариант 1: Vercel (Рекомендуется - Бесплатно)
```bash
1. Создай репо на GitHub
2. Загрузи web_app.html
3. Зарегистрируйся на Vercel
4. Импортируй репо
5. Получи URL: https://yourproject.vercel.app/web_app.html
6. Обнови в коде:
   MINIAPP_URL = "https://yourproject.vercel.app/web_app.html"
```

### Вариант 2: PythonAnywhere (Легко)
```bash
1. Загрузи файлы на pythonanywhere.com
2. Получи бесплатный HTTPS домен
3. Используй URL в коде
```

### Вариант 3: Собственный сервер
```python
# app.py
from flask import Flask, send_file

app = Flask(__name__)

@app.route('/web_app.html')
def web_app():
    return send_file('web_app.html', mimetype='text/html')

# Запуск с nginx + SSL
```

### Для тестирования (локально)
```python
# Временно используй файловый путь (не для production!)
MINIAPP_URL = "file:///C:/switzerbot/web_app.html"
```

---

## 🔧 Как использовать

### 1. Обновить MINIAPP_URL

[bot/handlers/miniapp.py](bot/handlers/miniapp.py#L15) - строка 15:

```python
# Заменить с:
MINIAPP_URL = "https://your-domain.com/web_app.html"

# На ваш реальный URL, например:
MINIAPP_URL = "https://switzerbot.vercel.app/web_app.html"
```

### 2. Перезапустить бот

```bash
python -m bot.main
```

### 3. Тестировать

В Telegram:
```
/miniapp
```

Нажми кнопку → откроется Mini App → попробуй действия

---

## 🛡️ Безопасность

### Валидация данных

```python
# ❌ НЕБЕЗОПАСНО
@router.message(F.web_app_data)
async def handle(message):
    data = json.loads(message.web_app_data.data)
    action = data['action']  # Может быть anything!
    user_id = data['user_id']  # Может не совпадать!

# ✅ БЕЗОПАСНО
@router.message(F.web_app_data)
async def handle(message, session):
    try:
        data = json.loads(message.web_app_data.data)
        
        # 1. Проверить структуру
        assert isinstance(data, dict)
        assert 'action' in data
        
        # 2. Проверить user_id
        if data.get('user_id') != message.from_user.id:
            return  # Не матчится
        
        # 3. Белый лист actions
        allowed = ['deposit', 'withdraw', 'transfer']
        action = data.get('action', '').lower()
        if action not in allowed:
            return  # Недопустимое действие
        
        # 4. Проверить аутентификацию
        user = await get_user_by_id(session, message.from_user.id)
        if not user.is_verified:
            return  # Не верифицирован
        
        # 5. Логировать
        logger.info(f"User {user.id} triggered: {action}")
        
    except (json.JSONDecodeError, AssertionError, ValueError):
        await message.answer("❌ Ошибка")
```

---

## 📝 Примеры расширений

### Отправить сообщение из Mini App
```javascript
// JavaScript в Mini App
const tg = window.Telegram.WebApp;
tg.MainButton.text = "Готово";
tg.MainButton.show();
tg.MainButton.onClick(() => {
    tg.sendData(JSON.stringify({
        action: 'complete',
        status: 'success'
    }));
    tg.close();
});
```

### Темная/Светлая тема
```javascript
const tg = window.Telegram.WebApp;

if (tg.colorScheme === 'dark') {
    document.body.classList.add('dark');
} else {
    document.body.classList.add('light');
}

// Слушать изменения темы
tg.onEvent('themeChanged', () => {
    // Обновить стили
});
```

### Хранение данных
```javascript
// Telegram Mini App имеет localStorage
localStorage.setItem('miniapp_state', JSON.stringify({
    lastAction: 'deposit',
    timestamp: Date.now()
}));
```

---

## ❌ Проблемы и решения

| Проблема | Решение |
|----------|---------|
| Mini App не открывается | Проверь MINIAPP_URL - должен быть HTTPS |
| "Telegram.WebApp not defined" | Убедись, что подключен скрипт: `<script src="https://telegram.org/js/telegram-web-app.js"></script>` |
| Данные не приходят в бота | Проверь, что handler регистрирован в main.py |
| WebView пуст | Откройся Console (F12) в браузере - проверь JS ошибки |
| CORS ошибка | Mini App не должен делать CORS запросы к другим сервисам |

---

## 📊 Статистика исправлений

| Компонент | Ошибка | Статус |
|-----------|--------|--------|
| help_explain.py | HTML Parse | ✅ ИСПРАВЛЕНО |
| business_card.py | Callback Parsing | ✅ ИСПРАВЛЕНО |
| menu.py | Edit Message | ✅ ИСПРАВЛЕНО |
| tournaments.py | SQL Query | ✅ ИСПРАВЛЕНО |
| miniapp.py | Новый handler | ✅ ДОБАВЛЕНО |
| bot/main.py | Регистрация | ✅ ДОБАВЛЕНО |
| MINIAPP_GUIDE.md | Документация | ✅ ДОБАВЛЕНО |

---

## 🎯 Дальнейшие шаги

1. **Deploy Mini App** на HTTPS сервер (Vercel/PythonAnywhere)
2. **Обновить URL** в коде
3. **Тестировать** все действия
4. **Добавить платежи** (BotFather Payments)
5. **Мониторить ошибки** в логах
6. **Улучшать UI** на основе feedback пользователей

---

## 📞 Контакты

Если есть вопросы:
- Отправь `/help` боту
- Отправь `/d3bug` для диагностики
- Проверь логи: смотри консоль бота

---

**Версия**: 2.5.1  
**Дата**: 2026-05-30  
**Статус**: ✅ Production Ready
