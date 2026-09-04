FROM python:3.11-slim

WORKDIR /app

# Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["python", "main.py"]