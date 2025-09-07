# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка supercronic для cron в контейнере
RUN curl -fsSLO https://github.com/aptible/supercronic/releases/download/v0.2.21/supercronic-linux-amd64 \
    && chmod +x supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Создаём папку для отчётов
RUN mkdir -p /app/xlsx_reports

# Переменная по умолчанию (можно переопределить в .env)
ENV XLSX_PATH=/app/xlsx_reports

# Копируем crontab для notifyer
COPY crontab /etc/crontabs/root

# По умолчанию запускаем основной бот
CMD ["python", "main.py"]