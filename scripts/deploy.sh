#!/bin/bash
# deploy.sh — ЗАПУСКАЙТЕ ЭТОТ СКРИПТ НА СЕРВЕРЕ ОДИН РАЗ

echo "🚀 Начинаем установку Obedbot из GitHub..."

# 1. Установка Docker, docker-compose, git
echo "📦 Устанавливаем зависимости..."
sudo apt update -y
sudo apt install -y docker.io docker-compose git

# 2. Добавляем пользователя в группу docker
sudo usermod -aG docker $USER

echo "🔁 Перезапускаем сессию для применения прав docker..."
exec newgrp docker << END
    echo "✅ Права docker применены."

    # 3. Переходим в домашнюю директорию
    cd ~

    # 4. Клонируем или обновляем репозиторий
    if [ -d "Obedbot" ]; then
        echo "📂 Папка Obedbot уже существует — обновляем код..."
        cd Obedbot
        git pull origin main
    else
        echo "📥 Клонируем репозиторий в ~/Obedbot..."
        git clone https://github.com/cvl196/Obedbot.git
        cd Obedbot
    fi

    # 5. 🔥 ГАРАНТИРОВАННОЕ СОЗДАНИЕ .env
    if [ ! -f ".env" ]; then
        echo "⚠️  Файл .env не найден."
        if [ -f ".env.example" ]; then
            echo "📋 Создаём .env из .env.example..."
            cp .env.example .env
            echo "✏️  Открываем .env для редактирования. ВСТАВЬТЕ СВОИ ТОКЕНЫ!"
            nano .env
        else
            echo "❌ Файл .env.example отсутствует! Создаём базовый .env..."
            echo "TOKEN=ваш_токен_основного_бота" > .env
            echo "ADMIN_TOKEN=ваш_токен_админ_бота" >> .env
            echo "ADMIN_CHAT_ID=ваш_chat_id" >> .env
            echo "XLSX_PATH=/app/xlsx_reports" >> .env
            echo "✏️  Создан минимальный .env. Открываем для заполнения..."
            nano .env
        fi
    else
        echo "✅ .env уже существует — используем его."
    fi

    # 6. Создаём папку для отчётов (если её нет)
    mkdir -p xlsx_reports

    # 7. Создаем crontab для notifyer
    echo "📋 Создаем crontab для планировщика..."
    cat > crontab << EOL
# Запуск каждый день в 00:01
1 0 * * * /usr/local/bin/python /app/notifyer.py
EOL

    # 8. Делаем update.sh исполняемым (если есть)
    if [ -f "update.sh" ]; then
        chmod +x update.sh
    fi

    # 9. 🚀 Запускаем сборку и старт контейнеров
    echo "🏗️  Собираем образы и запускаем контейнеры..."
    docker-compose up -d --build

    # 10. Проверка статуса
    echo "🎉 УСПЕХ! Система запущена."
    echo "👉 Основной бот:    docker logs -f school-bot"
    echo "👉 Админ-бот:       docker logs -f school-admin-bot"
    echo "👉 Уведомлялка:     docker logs -f school-notifyer"
    echo "👉 Отчёты лежат в:  ~/Obedbot/xlsx_reports"
    echo "👉 Обновление:      cd ~/Obedbot && ./update.sh"

    echo ""
    echo "📋 Текущий статус контейнеров:"
    docker-compose ps

END