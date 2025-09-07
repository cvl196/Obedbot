FROM python:3.11-slim

WORKDIR /app

# Меняем источники пакетов на зеркало Яндекса (для стабильной загрузки)
RUN rm -f /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm main" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Устанавливаем ТОЛЬКО curl (gcc не нужен!)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем supercronic
RUN curl -fsSLO https://github.com/aptible/supercronic/releases/download/v0.2.21/supercronic-linux-amd64 \
    && chmod +x supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . .

# Создание папки для отчётов
RUN mkdir -p /app/xlsx_reports

# Переменная окружения
ENV XLSX_PATH=/app/xlsx_reports

# Копирование crontab
COPY crontab /etc/crontabs/root

# Команда по умолчанию
CMD ["python", "main.py"]