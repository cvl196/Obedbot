import telebot
import pytz
from datetime import datetime, timedelta
from main import create_connection, create_keyboard_main, create_keyboard1,db_check_status_pupil
import sqlite3

TOKEN = '7631925603:AAGPVkbTAWWZREyoV9IJVa_WhAP5lgdbe64'
ADMIN_TOKEN = '7769524090:AAGr7jwyDwibyL0zZdZJMmuVyLHk350FeP8'
ADMIN_CHAT_ID = '791669507'

bot = telebot.TeleBot(TOKEN)
admin_bot = telebot.TeleBot(ADMIN_TOKEN)


conn = create_connection()
cursor = conn.cursor()

users_to_send = []

cursor.execute(F"""SELECT chat_id FROM users""")
users = cursor.fetchall()

tz = pytz.timezone('Asia/Yekaterinburg')
tomorrow = datetime.now(tz) + timedelta(days=1)
date = tomorrow.strftime("%d_%m_%Y")
table_name  = f"lunch_{date}"

cursor.execute(f"""SELECT chat_id FROM {table_name}""")
voted_users = cursor.fetchall()

for user in users: 
    if user not in voted_users and db_check_status_pupil(user[0]): 
        users_to_send.append(user[0])


current_hour = datetime.now(tz).hour


if current_hour < 17:
    greeting = "Добрый день"
elif 17 <= current_hour < 21:
    greeting = "Добрый вечер"
elif 21 <= current_hour < 23:
    greeting = "Доброй ночи"
else:
    greeting = "Здравствуйте"  
print(users_to_send)
for user in users_to_send: 
    last_msg = cursor.execute("SELECT last_msg FROM users WHERE chat_id = ?", (user,)).fetchone()[0] 
    if last_msg:  
        try:
            bot.delete_message(chat_id=user, message_id=last_msg)  
        except Exception as e:
            print(f"Ошибка при удалении сообщения для пользователя {user}: {e}")  # Логируем ошибку
    else:
        print(f"Нет сообщения для удаления у пользователя {user}")  # Логируем отсутствие last_msg
    message = bot.send_message(chat_id=user, 
                     text=f"""{greeting}, проголосуйте пожалуйста
Вы будете завтра обедать?""",
                     reply_markup=create_keyboard1())
    
    # Добавляем ID отправленного сообщения в таблицу users
    cursor.execute("UPDATE users SET last_msg = ? WHERE chat_id = ?", (message.message_id, user))
    conn.commit()

