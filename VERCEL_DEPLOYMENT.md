# 🚀 Быстрый гайд по развертыванию Mini App на Vercel

## За 5 минут на Vercel

### Шаг 1: Создать GitHub аккаунт (если нет)
1. Перейти на https://github.com/signup
2. Создать аккаунт
3. Подтвердить email

### Шаг 2: Создать репозиторий GitHub
1. Перейти на https://github.com/new
2. Назвать: `switzerbot-miniapp`
3. Выбрать Public
4. Create repository

### Шаг 3: Загрузить файл
1. В репо нажать "Add file" → "Upload files"
2. Выбрать файл: `web_app_mini.html`
3. Нажать "Commit changes"

### Шаг 4: Развернуть на Vercel
1. Перейти на https://vercel.com
2. Нажать "Sign Up" (или через GitHub)
3. Выбрать "Continue with GitHub"
4. Авторизироваться
5. Нажать "Import Project"
6. Выбрать репо `switzerbot-miniapp`
7. Нажать "Deploy"
8. Ждать ~1 минуты
9. Получить URL: `https://yourproject.vercel.app`

### Шаг 5: Обновить бот

**Файл**: `bot/handlers/miniapp.py` линия 15

```python
# Заменить:
MINIAPP_URL = "https://your-domain.com/web_app.html"

# На:
MINIAPP_URL = "https://yourproject.vercel.app/web_app_mini.html"
```

### Шаг 6: Перезапустить бот
```bash
cd c:\switzerbot
.\venv\Scripts\activate.ps1
python -m bot.main
```

### Шаг 7: Тестировать
```
/miniapp
```

---

## Альтернатива: PythonAnywhere (Еще проще)

### За 3 минуты на PythonAnywhere

1. **Зарегистрироваться**: https://www.pythonanywhere.com (Free tier)
2. **Загрузить файл**: 
   - Web → Files
   - Upload `web_app_mini.html`
3. **Получить URL**:
   - Web → Web apps
   - Скопировать ссылку на файл
   - Будет что-то вроде: `https://myusername.pythonanywhere.com/static/web_app_mini.html`
4. **Обновить в боте** и готово!

---

## Локальное тестирование (Без интернета)

```python
# Временно в miniapp.py для тестирования:
MINIAPP_URL = "file:///C:/switzerbot/web_app_mini.html"  # Windows

# После тестирования вернуть на Vercel URL
```

---

## Проверка что работает

После развертывания:

```bash
# 1. Открыть браузер
https://yourproject.vercel.app/web_app_mini.html

# 2. Проверить консоль (F12) - не должно быть ошибок
# 3. Открыть в боте:
/miniapp

# 4. Нажать кнопку - должна открыться Mini App
# 5. Кликнуть действие - должно закрыться и отправить данные в чат
```

---

## Доменная имя (Optional)

Если хочешь свой домен вместо `vercel.app`:

1. Купить домен на https://namecheap.com
2. В Vercel → Settings → Domains
3. Добавить свой домен
4. Обновить DNS (Vercel подскажет)
5. Использовать: `https://yourdomain.com/web_app_mini.html`

---

## Troubleshooting

### Mini App не открывается в Telegram
```
✓ Проверить MINIAPP_URL начинается с https://
✓ Проверить URL доступна в браузере
✓ Перезагрузить бота
✓ Отправить /miniapp заново
```

### Данные не приходят в бот
```
✓ Проверить регистрацию router в bot/main.py
✓ Проверить консоль браузера (F12) на JS ошибки
✓ Проверить логи бота на ошибки
✓ Попробовать отправить другое действие
```

### WebView открывается но пуста
```
✓ Открыть F12 → Console
✓ Проверить JS ошибки
✓ Проверить что файл загружается (Network tab)
✓ Пересоздать файл web_app_mini.html
```

---

## Ограничения Free Tier

| Vercel | PythonAnywhere |
|--------|----------------|
| ✅ HTTPS | ✅ HTTPS |
| ✅ Бесплатно | ✅ Бесплатно |
| ✅ Быстрый | ⚠️ Медленнее |
| ✅ Custom домен | ❌ Только поддомен |
| ✅ CDN | ❌ Нет CDN |
| ✅ Автоскейлинг | ❌ Ограничения |

**Вывод**: Vercel лучше! ✨

---

## После запуска

### Мониторинг
```bash
# Посмотреть логи Vercel:
# Vercel Dashboard → Project → Deployments → View Details

# Посмотреть ошибки бота:
# tail -f bot.log | grep ERROR
```

### Обновления
Если изменишь `web_app_mini.html`:
```bash
git add web_app_mini.html
git commit -m "Update mini app"
git push

# Vercel автоматически переразвернет за ~30 сек
```

### Кэширование
Если изменения не видны:
```
Ctrl+Shift+Delete (очистить кеш)
Или:
Vercel → Settings → Cache → Purge
```

---

## Финальная проверка

```bash
# 1. URL доступен?
curl https://yourproject.vercel.app/web_app_mini.html

# 2. Файл корректный HTML?
head -20 web_app_mini.html | grep "<!DOCTYPE"

# 3. Бот запущен?
curl https://api.telegram.org/bot<TOKEN>/getMe

# 4. Handler зарегистрирован?
grep "miniapp.router" bot/main.py

# 5. Mini App работает?
/miniapp → Click button → Проверить чат
```

---

## Готово! 🎉

Теперь:
- ✅ Mini App развернут на HTTPS
- ✅ Бот интегрирован с Mini App
- ✅ Пользователи могут открывать интерфейс
- ✅ Действия отправляются в бот

**Следующий шаг**: Добавить платежи BotFather для монетизации! 💰

---

## Быстрые ссылки

- GitHub: https://github.com
- Vercel: https://vercel.com
- Namecheap: https://namecheap.com
- PythonAnywhere: https://pythonanywhere.com
- Telegram Docs: https://core.telegram.org/bots/webapps

---

**Готово за 5 минут! 🚀**
