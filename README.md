Общее описание

Бот предназначен для автоматизации учета школьных обедов. Основные функции:

    Регистрация учеников и учителей

    Голосование за участие в обедах

    Формирование отчетов в Excel

    Управление классами и пользователями (админ-панель)

    Автоматические уведомления

Технологический стек

    Python 3.9+

    SQLite (база данных)

    Telebot (библиотека для Telegram API)

    Systemd (для управления процессами)

    Cron/Systemd Timers (для планировщика задач)

Требования к окружению

    Сервер с ОС Linux (Ubuntu 20.04+/Debian 10+)

    Python 3.9 и выше

    Установленные пакеты:

bash
Copy

sudo apt install -y python3-venv sqlite3

Установка и настройка
1. Клонирование репозитория
bash
Copy

git clone https://github.com/yourusername/school-lunch-bot.git
cd school-lunch-bot

2. Настройка виртуального окружения
bash
Copy

python3 -m venv bot_venv
source bot_venv/bin/activate
pip install -r requirements.txt

3. Создание .env файла
bash
Copy

nano .env

Содержимое:
ini
Copy

TOKEN=ваш_основной_токен_бота
ADMIN_TOKEN=ваш_админский_токен_бота
ADMIN_CHAT_ID=ваш_чат_id
XLSX_PATH=/путь/к/папке/с/файлами

4. Инициализация базы данных
bash
Copy

python3 main.py --init-db

Конфигурация systemd
1. Основной бот (main.py)

Создайте файл службы:
bash
Copy

sudo nano /etc/systemd/system/school-bot.service

Содержимое:
ini
Copy

[Unit]
Description=School Lunch Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/путь/к/проекту
Environment="PATH=/путь/к/проекту/bot_venv/bin"
ExecStart=/путь/к/проекту/bot_venv/bin/python3 /путь/к/проекту/main.py
Restart=always

[Install]
WantedBy=multi-user.target

2. Админ-бот (admin_main.py)
bash
Copy

sudo nano /etc/systemd/system/school-admin-bot.service

Содержимое аналогично основному боту, измените путь к скрипту:
ini
Copy

ExecStart=/путь/к/проекту/bot_venv/bin/python3 /путь/к/проекту/admin_main.py

3. Запуск служб
bash
Copy

sudo systemctl daemon-reload
sudo systemctl start school-bot
sudo systemctl start school-admin-bot
sudo systemctl enable school-bot
sudo systemctl enable school-admin-bot

Настройка планировщика (Notifyer)
Вариант 1: Cron
bash
Copy

crontab -e

Добавьте строки:
ini
Copy

0 8,12,16 * * * /путь/к/проекту/bot_venv/bin/python3 /путь/к/проекту/notifyer.py

Вариант 2: Systemd Timer

Создайте файл таймера:
bash
Copy

sudo nano /etc/systemd/system/notifyer.timer

Содержимое:
ini
Copy

[Unit]
Description=Run Notifyer every 4 hours

[Timer]
OnCalendar=*-*-* 08,12,16:00:00
Persistent=true

[Install]
WantedBy=timers.target

Управление службами

Проверка статуса:
bash
Copy

systemctl status school-bot
journalctl -u school-bot -f  # Просмотр логов

Перезагрузка:
bash
Copy

sudo systemctl restart school-bot

Структура проекта
Copy

.
├── bot_venv/          # Виртуальное окружение
├── data/              # Базы данных и файлы
├── xlsx/              # Генерируемые отчеты
├── main.py            # Основной бот
├── admin_main.py      # Админ-панель
├── notifyer.py        # Сервис уведомлений
├── databaser.py       # Работа с БД
├── .env               # Конфигурация
└── requirements.txt   # Зависимости
