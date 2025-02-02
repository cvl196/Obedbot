#!/bin/bash

VENV_PATH="/root/obed_bot/bot_venv/bin/activate"
BOT_PATH="/root/pooler_obed_bot/obed_bot.py"

# Проверяем существование сессии screen с именем 'poller'
if ! screen -list | grep -q "poller"; then
    echo "Сессия 'poller' не найдена, создаем новую..."

    # Создаем detached сессию screen и выполняем команды внутри неё
    screen -dmS poller bash -c "
        source $VENV_PATH &&
        python $BOT_PATH
    "
    echo "Бот запущен в новой сессии screen"
else
    echo "Сессия 'poller' уже существует. Перезапуск не требуется."
fi

# Показать список активных сессий
screen -list