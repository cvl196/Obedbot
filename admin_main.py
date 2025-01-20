import telebot

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import sqlite3
from sqlite3 import Error
import os
from main import create_connection,get_waitlist_info,create_keyboard_back,create_keyboard_reg1,get_user_info,get_exel_users   




load_dotenv()
TOKEN = os.getenv('TOKEN')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')


bot = telebot.TeleBot(TOKEN)
admin_bot = telebot.TeleBot(ADMIN_TOKEN)

def user_accept(chat_id, role):
    if role not in ['pupil', 'teacher']:
        raise ValueError("Role must be either 'pupil' or 'teacher'.")

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE 
            FROM users 
            WHERE chat_id = ?
        """, (chat_id,))
        conn.commit()

        cursor.execute("""
            SELECT first_name, last_name, grade, phone, chat_id, user_name, status, privil 
            FROM users_waitlist 
            WHERE chat_id = ?
        """, (chat_id,))
        user_data = cursor.fetchone()

        if user_data is None:
            print(f"Пользователь с chat_id {chat_id} не найден в списке ожидания.")
            return False

        # Проверяем наличие класса
        cursor.execute("SELECT class FROM classes WHERE class = ?", (user_data[2],))
        class_exists = cursor.fetchone()

        if class_exists is None:
            print(f"Класс {user_data[2]} не найден.")
            return False

        if user_data[5] is None:
            user_name = 'Нет имени пользователя'
        else:
            user_name = user_data[5]
        cursor.execute("""
            INSERT INTO users (first_name, last_name, grade, phone, chat_id, user_name, status, privil)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_name, role, user_data[7]))

        # Удаляем пользователя из списка ожидания
        cursor.execute("DELETE FROM users_waitlist WHERE chat_id = ?", (chat_id,))
        if role == 'pupil':
            cursor.execute("UPDATE classes SET people = people + 1 WHERE class = ?", (user_data[2],))
        conn.commit()
        print(f"Пользователь с chat_id {chat_id} одобрен и перемещен в users.")
        return True

    except sqlite3.Error as e:
        print(f"Произошла ошибка SQL: {e}")
        bot.send_message(
            chat_id=chat_id,
            text='Произошла ошибка при регистрации, попробуйте еще раз',
            reply_markup=create_keyboard_reg1()
        )
        return False
    finally:
        cursor.close()
        conn.close()

def user_delete(chat_id):
    """Удаляет пользователя из таблицы users по chat_id."""
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE 
            FROM users 
            WHERE chat_id = ?
        """, (chat_id,))
        conn.commit()

        cursor.execute("SELECT grade FROM users WHERE chat_id = ?", (chat_id,))
        user_data = cursor.fetchone()

        # Уменьшаем количество людей в классе на 1
        if user_data is not None:
            cursor.execute("UPDATE classes SET people = people - 1 WHERE class = ?", (user_data[0],))

        # Удаляем пользователя из таблицы users
        cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
        
        # Проверяем количество удаленных строк
        if cursor.rowcount == 0:
            print(f"No user found with chat_id {chat_id}.")
        else:
            print(f"User with chat_id {chat_id} has been deleted.")

        # Сохраняем изменения
        conn.commit()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Закрываем соединение
        cursor.close()
        conn.close()

def user_reject(chat_id):
    conn = create_connection()
    cursor = conn.cursor()    
    cursor.execute("DELETE FROM users_waitlist WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
  
def block_user(chat_id):   
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE 
            FROM users 
            WHERE chat_id = ?
        """, (chat_id,))
        conn.commit()

        cursor.execute("SELECT chat_id, user_name, phone FROM users_waitlist WHERE chat_id = ?", (chat_id,))
        user_data = cursor.fetchone()

        if user_data is None:
            print(f"Пользователь с chat_id {chat_id} не найден в списке ожидания.")
            return

        # Добавляем пользователя в таблицу заблокированных
        cursor.execute("""
            INSERT INTO blocked_users (chat_id, user_name, phone)  
            VALUES (?, ?, ?)
        """, (chat_id, user_data[1], user_data[2]))

        # Удаляем пользователя из списка ожидания
        cursor.execute("DELETE FROM users_waitlist WHERE chat_id = ?", (chat_id,))

        conn.commit()
        print(f"Пользователь с chat_id {chat_id} заблокирован.")

    except sqlite3.Error as e:
        print(f"Произошла ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

def unblock_user(info):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blocked_users WHERE chat_id = ? OR phone = ? OR user_name = ?", (info, info, info))
    conn.commit()
    conn.close()

def unblocking_user(message):
    info = message.text
    unblock_user(info)
    admin_bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Пользователь {info} разблокирован")


def create_keyboard_users(users):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for user in users:
        name = f"{user[0]} {user[1]}"
        keyboard.add(telebot.types.InlineKeyboardButton(text=name, callback_data=f"profile${user[2]}"))
        
    return keyboard

def create_keyboard_close():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton(text="Закрыть", callback_data="close"))
    return keyboard

def create_keyboard_delete_acception(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton(text="Подтвердить удаление пользователя", callback_data=f"delete${chat_id}"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Закрыть", callback_data="close"))
    return keyboard

def create_keyboard_profile(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить", callback_data=f"delete_acception${chat_id}"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Закрыть", callback_data="close"))
    return keyboard

def create_keyboard_classes(): 
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT class FROM classes""")
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    print (classes)
    for cl in classes: 
        keyboard.add(telebot.types.InlineKeyboardButton(text=f"{cl[0]}", callback_data=f"class${cl[0]}"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Закрыть", callback_data="close"))
    return keyboard

def create_keyboard_class(name): 
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить", callback_data=f"delete_class_accept${name}"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="close"))
    return keyboard

def create_keyboard_class_accept(name): 
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить", callback_data=f"delete_class${name}"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="close"))
    return keyboard

def creating_class(message): 
    # Извлекаем текст из объекта message
    class_name = message.text.upper()  
    conn = create_connection()
    cursor = conn.cursor()
    
    # Используем параметризованный запрос
    cursor.execute(f"""SELECT class FROM classes WHERE class = ?""", (class_name,))
    clas = cursor.fetchone()
    
    if clas: 
        admin_bot.send_message(chat_id=ADMIN_CHAT_ID,
                               text=f'Такой класс уже существует'
                               )
    else: 
        cursor.execute(f"""INSERT INTO classes (class, people)
                       VALUES (?, ?)""", (class_name, 0))  # Используем class_name вместо message

        admin_bot.send_message(chat_id=ADMIN_CHAT_ID,
                               text=f'Вы успешно создали класс {class_name}'
                               )
        conn.commit()
    
    cursor.close()
    conn.close()

def opening_profile(message):
    conn = create_connection()
    cursor = conn.cursor()

    par = message.text

    cursor.execute("""SELECT first_name, last_name, chat_id, user_name, status, phone FROM users 
                   WHERE first_name = ?
                   OR last_name = ? 
                   OR chat_id = ? 
                   OR user_name = ?
                   OR phone = ?""", 

                   (par, par, par, par, par))    
    users = cursor.fetchall()
    if len(users) == 0:
        admin_bot.send_message(chat_id=ADMIN_CHAT_ID, text="Пользователей по данным не найдено",reply_markup=create_keyboard_close())
    else:
        keyboard = create_keyboard_users(users)
        admin_bot.send_message(chat_id=ADMIN_CHAT_ID, text="Выберите пользователя", reply_markup=keyboard)
    conn.close()   

@admin_bot.message_handler(commands=['profiles'])
def profiles(message):
    admin_bot.send_message(chat_id=ADMIN_CHAT_ID, text="Введите информацию о пользователе ")
    
    admin_bot.register_next_step_handler(message, opening_profile)

@admin_bot.message_handler(commands=['unblock'])
def unblock_user_command(message):
    admin_bot.send_message(chat_id=ADMIN_CHAT_ID, text="Введите user_name или телефон пользователя для разблокировки")
    admin_bot.register_next_step_handler(message, unblocking_user)

@admin_bot.message_handler(commands=['classes'])
def show_classes (message):
    admin_bot.send_message(chat_id=ADMIN_CHAT_ID, 
                           text='Выберите класс:',
                           reply_markup=create_keyboard_classes())
    
@admin_bot.message_handler(commands=['users_exel'])
def send_users (message):
    get_exel_users()
    with open('people.xlsx', 'rb') as file:
                admin_bot.send_document(
                chat_id=message.chat.id,
                document=file
                )


@admin_bot.message_handler(commands=['create_class'])
def create_class(message):
    admin_bot.send_message(chat_id=ADMIN_CHAT_ID, text="Введите класс который хотите создать")
    admin_bot.register_next_step_handler(message, creating_class)

@admin_bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith('accept$'):
        chat_id = call.data.split('$')[1]
        winfo = get_waitlist_info(chat_id)
        
        if winfo is None:
            admin_bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Ошибка: пользователь не найден в списке ожидания",
                reply_markup=create_keyboard_reg1()
            )
            return
        
        if user_accept(chat_id, 'pupil'):
            admin_bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"""Пользователь был успешно добавлен ✅
Имя: {winfo[1]}
Фамилия: {winfo[2]}
Класс: {winfo[3]}
Телефон: {winfo[4]}
Имя пользователя: {winfo[6]}
Льготник: {'Да' if winfo[7] else 'Нет' }"""
            )
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT last_msg FROM users  WHERE chat_id = ?", (chat_id,))
            last_msg = cursor.fetchone()
            if not last_msg: 
                bot.delete_message(chat_id=chat_id, 
                                   message_id = last_msg)



            tmp_msg = bot.send_message(
                chat_id=chat_id,
                text="Ваш запрос на регистрацию принят. Вы можете использовать бота.",
                reply_markup=create_keyboard_back()
            )
            tmp_msg = tmp_msg.message_id
            
            cursor.execute("UPDATE users SET last_msg = ? WHERE chat_id = ?", (tmp_msg, chat_id))
            conn.commit()
            conn.close()



        else:
            admin_bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Произошла ошибка при добавлении пользователя"
                
            )
    
    elif call.data.startswith('block$'):        
        chat_id = call.data.split('$')[1]
        winfo = get_waitlist_info(chat_id)
        block_user(chat_id)
        admin_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"""Пользователь был заблокирован
Имя: {winfo[1]}
Фамилия: {winfo[2]}
Класс: {winfo[3]}
Телефон: {winfo[4]}
Имя пользователя: {winfo[6]}
Льготник: {'Да' if winfo[7] else 'Нет' }""")
        bot.send_message(
            chat_id=chat_id,
            text="Вы были заблокированы, если блокировка произошла по ошибке, обратитесь к администратору",
            reply_markup=create_keyboard_reg1()
        )
        
    elif call.data.startswith('reject$'):
        winfo = get_waitlist_info(call.message.chat.id)
        chat_id = call.data.split('$')[1]
        user_reject(chat_id)
        admin_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"""Запрос от пользователя был отклонен
Имя: {winfo[1]}
Фамилия: {winfo[2]}
Класс: {winfo[3]}
Телефон: {winfo[4]}
Имя пользователя: {winfo[6]}
Льготник: {'Да' if winfo[7] else 'Нет' }"""
        )
        bot.send_message(
            chat_id=chat_id,
            text="Ваш запрос на регистрацию отклонен, перепроверьте данные и отправьте запрос еще раз.",
            reply_markup=create_keyboard_reg1()
        )
    
    elif call.data.startswith('accept_teacher$'):
        chat_id = call.data.split('$')[1]
        user_accept(chat_id,'teacher')

        winfo = get_user_info(call.message.chat.id)

        admin_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"""Пользователь был успешно добавлен как учитель ✅
Имя: {winfo[2]}
Фамилия: {winfo[3]}
Класс: {winfo[4]}
Телефон: {winfo[5]}
Имя пользователя: {winfo[7]}"""
        )
        
        bot.send_message(
            chat_id=chat_id,
            text="Ваш запрос на регистрацию принят. Вы можете использовать бота.",
            reply_markup=create_keyboard_back()
        )

    elif call.data.startswith('delete$'):
        chat_id = call.data.split('$')[1]
        winfo = get_user_info(chat_id)
        if winfo[6] == 'teacher':
            status = 'Учитель'
        else:
            status = 'Ученик'
        user_delete(chat_id)
        admin_bot.edit_message_text(chat_id=ADMIN_CHAT_ID, 
                                    message_id=call.message.message_id,
                                    text=f"""Пользователь удален:
Имя: {winfo[2]}
Фамилия: {winfo[3]}
Класс: {winfo[4]}
Статус: {status}
Телефон: {winfo[5]}
Имя пользователя: {winfo[7]}
Льготник: {'Да' if winfo[7] else 'Нет' }""",
                                    reply_markup=create_keyboard_close())

    elif call.data.startswith('delete_acception$'):
        chat_id = call.data.split('$')[1]
        winfo = get_user_info(chat_id)
        
        if winfo[6] == 'teacher':
            status = 'Учитель'
        else:
            status = 'Ученик'
        admin_bot.edit_message_text(chat_id=ADMIN_CHAT_ID,                                     
                              message_id=call.message.message_id,
                                text=f"""Вы уверенны что ходите удалить пользователя? 
Имя: {winfo[2]}
Фамилия: {winfo[3]}
Класс: {winfo[4]}
Статус: {status}
Телефон: {winfo[5]}
Имя пользователя: {winfo[7]}
Льготник: {'Да' if winfo[7] else 'Нет' }""",
                                
                                reply_markup=create_keyboard_delete_acception(chat_id))
    
    elif call.data.startswith('profile$'):
        chat_id = call.data.split('$')[1]
        winfo = get_user_info(chat_id)
        if winfo[6] == 'teacher':
            status = 'Учитель'
        else:
            status = 'Ученик'
        admin_bot.edit_message_text (chat_id=ADMIN_CHAT_ID, 
                                    message_id=call.message.message_id,
                               text=f"""Имя: {winfo[2]}
Фамилия: {winfo[3]}
Класс: {winfo[4]}
Статус: {status}
Телефон: {winfo[5]}
Имя пользователя: {winfo[7]}
Льготник: {'Да' if winfo[8] else 'Нет' }""",
                               reply_markup=create_keyboard_profile(chat_id))
        
    elif call.data.startswith('delete_class$'): 
        cl_name = call.data.split('$')[1] 
        conn = create_connection()
        cursor = conn.cursor()
        
        # Удаляем всех пользователей с grade, совпадающим с названием класса
        cursor.execute("DELETE FROM users WHERE grade = ?", (cl_name,))
        
        cursor.execute("DELETE FROM classes WHERE class = ?", (cl_name,))
        conn.commit()
        cursor.close()
        conn.close()
        
        admin_bot.edit_message_text(chat_id=ADMIN_CHAT_ID,
                                     message_id=call.message.message_id, 
                                     text=f'Вы успешно удалили {cl_name}',
                                     reply_markup=create_keyboard_close())
        
    elif call.data.startswith('class$'): 
        print(call.data)
        cl_name = call.data.split('$')[1]
        print(cl_name)
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"""SELECT people FROM classes WHERE class = ?""", (cl_name,))
        num = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Проверяем, есть ли данные
        if num is not None:
            people_count = num[0]  # Получаем количество людей
        else:
            people_count = 0  # Если данных нет, устанавливаем 0

        admin_bot.edit_message_text(
            chat_id=ADMIN_CHAT_ID, 
            message_id=call.message.message_id,
            text=f'Класс {cl_name}, количество человек {people_count}',  # Используем people_count
            reply_markup=create_keyboard_class(cl_name)
        )
    
    elif call.data.startswith('delete_class_accept$'):
        cl_name = call.data.split('$')[1]
        
        
        admin_bot.edit_message_text(chat_id=call.message.chat.id, 
                                  message_id=call.message.message_id, 
                                  text=f"""Вы уверены, что хотите удалить класс? 
При удалении класса также будут удалены все ученики, относящиеся к нему""",
                                  reply_markup=create_keyboard_class_accept(cl_name))
          
    elif call.data == 'close':
        admin_bot.delete_message(chat_id=ADMIN_CHAT_ID, message_id=call.message.message_id)
    
    admin_bot.answer_callback_query(call.id)

def delete_class(class_name):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM classes WHERE class = ?", (class_name,))
        
        cursor.execute("DELETE FROM users WHERE grade = ?", (class_name,))
        
        conn.commit()
        print(f"Класс {class_name} и все его пользователи успешно удалены.")

    except sqlite3.Error as e:
        print(f"Произошла ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':

    admin_bot.polling(none_stop=True)
   
