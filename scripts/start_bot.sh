#!/bin/bash

# Параметры
VENV_PATH="/root/obed_bot/bot_venv/bin/activate"
BOT_PATH="/root/obed_bot/main.py"
ADMIN_BOT_PATH="/root/obed_bot/admin_main.py"
LOG_FILE="/root/obed_bot/bot.log"
SESSION_NAME="main_bot_session"
ADMIN_SESSION_NAME="admin_bot_session"

# Функция для записи в лог
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Проверка наличия виртуального окружения
if [ ! -f "$VENV_PATH" ]; then
    log "Ошибка: Виртуальное окружение не найдено по пути $VENV_PATH."
    exit 1
fi

# Проверка наличия основного скрипта бота
if [ ! -f "$BOT_PATH" ]; then
    log "Ошибка: Скрипт не найден по пути $BOT_PATH."
    exit 1
fi

# Проверка наличия скрипта администратора
if [ ! -f "$ADMIN_BOT_PATH" ]; then
    log "Ошибка: Скрипт администратора не найден по пути $ADMIN_BOT_PATH."
    exit 1
fi

# Запуск основного бота в новой сессии screen
if ! screen -list | grep -q "$SESSION_NAME"; then
    log "Запуск нового экземпляра основного бота в сессии screen: $SESSION_NAME."
    screen -dmS "$SESSION_NAME" bash -c "source $VENV_PATH && python $BOT_PATH"
else
    log "Сессия с именем $SESSION_NAME уже запущена."
fi

# Запуск бота администратора в новой сессии screen
if ! screen -list | grep -q "$ADMIN_SESSION_NAME"; then
    log "Запуск нового экземпляра бота администратора в сессии screen: $ADMIN_SESSION_NAME."
    screen -dmS "$ADMIN_SESSION_NAME" bash -c "source $VENV_PATH && python $ADMIN_BOT_PATH"
else
    log "Сессия с именем $ADMIN_SESSION_NAME уже запущена."
fi

log "Скрипт завершен."
