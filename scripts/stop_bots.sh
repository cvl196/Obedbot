#!/bin/bash

# Имена сессий
SESSION_NAME="main_bot_session"
ADMIN_SESSION_NAME="admin_bot_session"

# Функция для записи в лог
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "/root/obed_bot/bot.log"
}

# Завершение работы основного бота
if screen -list | grep -q "$SESSION_NAME"; then
    log "Завершение работы основного бота в сессии: $SESSION_NAME."
    screen -S "$SESSION_NAME" -X quit
else
    log "Сессия с именем $SESSION_NAME не найдена."
fi

# Завершение работы бота администратора
if screen -list | grep -q "$ADMIN_SESSION_NAME"; then
    log "Завершение работы бота администратора в сессии: $ADMIN_SESSION_NAME."
    screen -S "$ADMIN_SESSION_NAME" -X quit
else
    log "Сессия с именем $ADMIN_SESSION_NAME не найдена."
fi

log "Скрипт завершен."
