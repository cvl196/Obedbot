FROM python:3.11-slim

WORKDIR /app

# Меняем источники пакетов на зеркало Яндекса
RUN rm -f /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm main" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Устанавливаем cron и tzdata
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем временную зону для Екатеринбурга
RUN ln -fs /usr/share/zoneinfo/Asia/Yekaterinburg /etc/localtime
RUN echo "Asia/Yekaterinburg" > /etc/timezone

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . .

# Создание папки для отчётов
RUN mkdir -p /app/xlsx_reports

# Переменная окружения
ENV XLSX_PATH=/app/xlsx_reports
ENV TZ=Asia/Yekaterinburg

# Настраиваем cron
COPY crontab /etc/cron.d/obedbot-cron
RUN chmod 0644 /etc/cron.d/obedbot-cron
RUN touch /var/log/cron.log

# Создаем скрипт для запуска cron
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'cron && tail -f /var/log/cron.log' >> /app/start.sh && \
    chmod +x /app/start.sh

RUN mkdir -p /app/xlsx_reports /app/db_data

# Установите правильные права доступа
RUN chmod 755 /app/xlsx_reports /app/db_data

# Команда по умолчанию
CMD ["python", "main.py"]