Общее описание

Бот предназначен для автоматизации учета школьных обедов. Основные функции:

- Регистрация учеников и учителей

- Голосование за участие в обедах

- Формирование отчетов в Excel

- Управление классами и пользователями (админ-панель)

- Автоматические уведомления


Требования к окружению

 - Сервер с ОС Linux (Ubuntu 20.04+/Debian 10+)

 - Python 3.9 и выше

Установка и настройка
1. Клонирование репозитория
````
  git clone https://github.com/cvl196/Obedbot
````
2. Создание .env файла
````
   nano .env
````
Содержимое:
````
  TOKEN=ваш_основной_токен_бота
  ADMIN_TOKEN=ваш_админский_токен_бота
  ADMIN_CHAT_ID=чат_айди_админа
  XLSX_PATH=/путь/к/папке/с/файлами
````
Конфигурация systemd
1. Основной бот (main.py)

Создайте файл службы:
````
  sudo nano /etc/systemd/system/school-bot.service
````
Содержимое:
````
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
````
2. Админ-бот (admin_main.py)
````
  sudo nano /etc/systemd/system/school-admin-bot.service
````
Содержимое аналогично основному боту, измените путь к скрипту:
````
  ExecStart=/путь/к/проекту/bot_venv/bin/python3 /путь/к/проекту/admin_main.py
````
3. Запуск служб
````
sudo systemctl daemon-reload
sudo systemctl start school-bot
sudo systemctl start school-admin-bot
sudo systemctl enable school-bot
sudo systemctl enable school-admin-bot
````
