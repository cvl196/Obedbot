#!/bin/bash
# update.sh — Запускайте этот скрипт на сервере после git push

echo "🔄 Обновляем код из GitHub..."
git pull origin main

echo "🏗️ Пересобираем и перезапускаем сервисы..."
docker-compose up -d --build

echo "✅ Обновление завершено!"
echo "👉 Проверьте логи, если нужно:"
echo "   docker logs -f school-bot"
echo "   docker logs -f school-admin-bot"
echo "   docker logs -f school-notifyer"