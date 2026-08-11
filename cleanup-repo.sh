#!/bin/bash
# 🗑️ БЛОК G: Очистка репозитория
# Удаление swiwallet-app, проверка секретов, финальный commit

set -e

cd /opt/botik || cd ~/botik || exit 1

echo "════════════════════════════════════════════════════════════"
echo "🗑️  БЛОК G: ОЧИСТКА РЕПОЗИТОРИЯ"
echo "════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# G1: Удалить папку swiwallet-app
# ═══════════════════════════════════════════════════════════════
echo "📍 G1: Удаление папки swiwallet-app..."

if [ -d "swiwallet-app" ]; then
    git rm -r swiwallet-app 2>/dev/null || rm -rf swiwallet-app
    echo "✅ swiwallet-app удалена"
else
    echo "⚠️ swiwallet-app уже отсутствует"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# G2: Убедиться, что файлы на месте
# ═══════════════════════════════════════════════════════════════
echo "📍 G2: Проверка основных файлов..."

FILES=(
    "bot.py"
    "web_app.html"
    ".env"
    ".gitignore"
    "production-setup.sh"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file присутствует"
    else
        echo "⚠️ $file отсутствует (создай вручную)"
    fi
done

echo ""

# ═══════════════════════════════════════════════════════════════
# G3: Аудит секретов
# ═══════════════════════════════════════════════════════════════
echo "📍 G3: Проверка на утёкшие секреты..."

# Проверяем, что BOT_TOKEN не в истории коммитов
if git log -p 2>/dev/null | grep -i "BOT_TOKEN" | grep -v "# " > /dev/null 2>&1; then
    echo "⚠️ ВНИМАНИЕ: BOT_TOKEN может быть в истории коммитов!"
    echo "   Действия:"
    echo "   1. Если токен засвечен — немедленно ротируй его в BotFather"
    echo "   2. Используй git filter-branch или BFG для очистки истории"
    echo "   3. Измени все токены в .env и коммитов"
else
    echo "✅ BOT_TOKEN не найден в истории (безопасно)"
fi

# .env не должен быть в git
if git ls-files | grep "\.env" > /dev/null 2>&1; then
    echo "⚠️ ВНИМАНИЕ: .env в git! Удаляю..."
    git rm --cached .env
else
    echo "✅ .env не в git (правильно)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# G4: Финальный commit
# ═══════════════════════════════════════════════════════════════
echo "📍 G4: Финальный commit..."

git add -A

if [ -n "$(git status --porcelain)" ]; then
    git commit -m "chore(G): cleanup - remove swiwallet-app, finalize structure"
    echo "✅ Commit создан"
else
    echo "ℹ️ Нет изменений для коммита"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# ФИНАЛЬНАЯ ПРОВЕРКА
# ═══════════════════════════════════════════════════════════════
echo "════════════════════════════════════════════════════════════"
echo "✅ БЛОК G ЗАВЕРШЁН"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 Финальная структура:"
git ls-files | head -20
echo ""
echo "📊 Статистика:"
echo "  Коммиты: $(git log --oneline | wc -l)"
echo "  Файлов: $(git ls-files | wc -l)"
echo ""
echo "🚀 Дальше:"
echo "  git push origin main  (если нужно отправить на GitHub)"
echo "  git log --oneline -5  (проверить историю)"
echo ""
