FROM python:3.11-slim

WORKDIR /app

# Меняем источники пакетов на зеркало Яндекса
RUN rm -f /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm main" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Устанавливаем curl и supercronic
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем supercronic для планировщика задач
RUN curl -fsSLO https://github.com/aptible/supercronic/releases/download/v0.2.21/supercronic-linux-amd64 \
    && chmod +x supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем папку для отчетов
RUN mkdir -p /app/xlsx_reports

# Копируем crontab для notifyer
COPY crontab /etc/crontabs/root

# Переменные окружения
ENV XLSX_PATH=/app/xlsx_reports