#!/bin/bash

VENV_PATH="/root/obed_bot/bot_venv/bin/activate"
BOT_PATH="/root/obed_bot/notifyer.py"

# Проверяем существование сессии screen с именем 'notify'
if ! screen -list | grep -q "notify"; then
    echo "Сессия 'notify' не найдена, создаем новую..."

    # Создаем detached сессию screen и выполняем команды внутри неё
    screen -dmS notify bash -c "
        source $VENV_PATH &&
        python $BOT_PATH
    "
    echo "Бот запущен в новой сессии screen"
else
    echo "Сессия 'notify' уже существует. Перезапуск не требуется."
fi

# Показать список активных сессий
screen -list