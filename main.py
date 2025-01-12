import telebot
from datetime import datetime, timedelta
import pytz
import sqlite3
from sqlite3 import Error
import os
import pandas as pd
from openpyxl.utils import get_column_letter  # Импортируем функцию для получения букв столбцов
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side  # Импортируем классы для выравнивания и границ

# Получаем текущий путь
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, 'lunch_database.db')

# Токены
TOKEN = '7631925603:AAGPVkbTAWWZREyoV9IJVa_WhAP5lgdbe64'
ADMIN_TOKEN = '7769524090:AAGr7jwyDwibyL0zZdZJMmuVyLHk350FeP8'
ADMIN_CHAT_ID = '791669507'
# Инициализация ботов
bot = telebot.TeleBot(TOKEN)
admin_bot = telebot.TeleBot(ADMIN_TOKEN)



def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Error as e:
        print(f"Ошибка при подключении к БД: {e}")
        return None

def init_db():
    """Инициализация базы данных при запуске"""
    if not os.path.exists(DB_PATH):
        conn = create_connection()
        if conn:
            conn.close()
        print("База данных создана")
    
def db_check_id(chat_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
            
            result = cursor.fetchone()
            return result is not None
            
        except Error as e:
            print(f"Ошибка при проверке ID: {e}")
            return False
        finally:
            conn.close()
    return False

def db_check_status_pupil(chat_id):
    conn = create_connection()
    if conn is not None:        
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()        
        if result[0] == 'pupil':
            conn.close()
            return True            
        else:
            conn.close()
            
            return False

def db_check_status_teacher(chat_id):
    conn = create_connection()
    if conn is not None:        
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        
        if result[0] == 'teacher':
            conn.close()
            return True            
        else:
            conn.close()
            
            return False

def db_get_lunch_info_teacher(table_name):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name, will_eat FROM {table_name}")
            results = cursor.fetchall()
            
            formatted_results = []
            for name, will_eat in results:
                status = "Обедает" if will_eat else "Не обедает"
                formatted_results.append(f"{name} - {status}")
            
            return "\n".join(formatted_results) if formatted_results else "Нет данных"
            
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return "Ошибка при получении данных"
        finally:
            conn.close()
    return "Ошибка подключения к базе данных"

def create_table(date):
    conn = create_connection()
    if conn is not None:
        try:
            year = datetime.now().strftime("%Y")
            table_name = f"lunch_{date.replace('.', '_')}_{year}"
            cursor = conn.cursor()
            
            cursor.execute(f''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}' ''')
            
            if cursor.fetchone()[0] == 0:
                cursor.execute(f'''
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        will_eat BOOLEAN NOT NULL,
                        will_attend BOOLEAN,
                        reason TEXT
                    )
                ''')
            
            conn.commit()
            print(f"Таблица {table_name} проверена и обновлена")
            return table_name
        except Error as e:
            print(f"Ошибка при работе с таблицей: {e}")
        finally:
            conn.close()
    return None

def add_lunch_record(table_name, chat_id, will_eat, will_attend=None, reason=None):
    if isinstance(will_eat, str):
        will_eat = will_eat.lower() == "да"
    if isinstance(will_attend, str) and will_attend is not None:
        will_attend = will_attend.lower() == "да"
    
    if will_eat:
        will_attend = True
        reason = None
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Проверяем существование таблицы
            cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', (table_name,))
            if cursor.fetchone()[0] == 0:
                # Создаем таблицу, если она не существует
                cursor.execute(f'''
                    CREATE TABLE "{table_name}" (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        will_eat BOOLEAN NOT NULL,
                        will_attend BOOLEAN,
                        reason TEXT
                    )
                ''')
            
            # Проверяем существующую запись
            cursor.execute(f"SELECT id FROM {table_name} WHERE chat_id = ?", (chat_id,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                cursor.execute(f'''
                    UPDATE {table_name}
                    SET will_eat = ?, will_attend = ?, reason = ?
                    WHERE chat_id = ?
                ''', (will_eat, will_attend, reason, chat_id))
            else:
                cursor.execute(f'''
                    INSERT INTO {table_name} (chat_id, will_eat, will_attend, reason)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, will_eat, will_attend, reason))
            
            conn.commit()
        except Error as e:
            print(f"Ошибка при добавлении записи: {e}")
        finally:
            conn.close()

def get_lunch_info(chat_id, today=False):
    
    tz = pytz.timezone('Asia/Yekaterinburg')
    
    if today:
        tomorrow = datetime.now(tz)
    else:
        tomorrow = datetime.now(tz) + timedelta(days=1)
    date = tomorrow.strftime("%d.%m")
    year = tomorrow.strftime("%Y")
    table_name = f"lunch_{date.replace('.', '_')}_{year}"
    
    conn = create_connection()
    if conn is not None:
        try:
            record_info = "Нет данных о голосовании"
            cursor = conn.cursor()
            
            # Проверяем существование таблицы
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            
            if not cursor.fetchone():
                # Создаем таблицу, если она не существует
                cursor.execute(f'''
                    CREATE TABLE "{table_name}" (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        will_eat BOOLEAN NOT NULL,
                        will_attend BOOLEAN,
                        reason TEXT
                    )
                ''')
            
            # Получаем данные пользователя
            cursor.execute(f"SELECT * FROM {table_name} WHERE chat_id = ?", (chat_id,))
            record = cursor.fetchone()
            
            if record:  # Если запись найдена
                # Получаем названия колонок
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in cursor.fetchall()]
                
                record_dict = dict(zip(columns, record))
                
                obed_info = "✅" if record_dict['will_eat'] else "❌"
                appdend_info = "✅" if record_dict['will_attend'] else "❌"
                reason_info = 'Больничный' if record_dict['reason'] == 'ill' else 'Заявление' if record_dict['reason'] == 'doc' else '-'
               
                if record_dict['will_eat']:
                    record_info = f"""
{date} 
Информация о обедах: {obed_info}
        
"""
                elif record_dict['will_attend'] == False:                 
                    record_info = f"""
{date} 
Информация о обедах: {obed_info}
Будет в школе: {appdend_info}
Причина отсутствия: {reason_info}
"""
                else:
                    record_info = f"""
{date} 
Информация о обедах: {obed_info}
Будет в школе: {appdend_info}
"""
                
            
            return record_info
            
        except Error as e:
            return f"Ошибка при получении данных: {e}"
        finally:
            conn.close()
    return "Ошибка подключения к базе данных"

def add_user_waitlist(new_value, column_name, chat_id):
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            
            cursor.execute('SELECT chat_id FROM users_waitlist WHERE chat_id = ?', (chat_id,))
            user_exists = cursor.fetchone() is not None
            
            if user_exists:
                
                cursor.execute(f'''
                    UPDATE users_waitlist 
                    SET {column_name} = ?
                    WHERE chat_id = ?
                ''', (new_value, chat_id))
            else:
                
                cursor.execute(f'''
                    INSERT INTO users_waitlist (chat_id, {column_name})
                    VALUES (?, ?)
                ''', (chat_id, new_value))
            
            conn.commit()
            return True
                
        except Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
            return False
        finally:
            conn.close()
    return False

def check_blocked_user(chat_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM blocked_users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    if result is not None:
        return True
    else:
        return False

def get_waitlist_info(chat_id):
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Получаем данные пользователя
            cursor.execute('''
                SELECT *
                FROM users_waitlist 
                WHERE chat_id = ?
            ''', (chat_id,))
            
            result = cursor.fetchone()
            
            if result:
                return list(result)
            else:
                print(f"Пользователь с chat_id {chat_id} не найден")
                return None
                
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return None
        finally:
            conn.close()
    return None

def get_user_info(chat_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    user_info = cursor.fetchone()
    return user_info

def generate_attendance_report(start_date_str, end_date_str, grade):
    # Преобразуем строки в формат Timestamp
    start_date = pd.to_datetime(start_date_str, format="%d.%m.%Y")
    end_date = pd.to_datetime(end_date_str, format="%d.%m.%Y")

    # Подключение к базе данных
    conn = create_connection()
    cursor = conn.cursor()

    # Получаем список всех таблиц в базе данных
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Список для хранения всех записей
    records = []

    # Получаем список пользователей
    cursor.execute("SELECT first_name, last_name, chat_id FROM users WHERE grade = ?", (grade,))
    
    users_id = []
    users = [{'name': f"{row[1]} {row[0]}", 'chat_id': row[2]} for row in cursor.fetchall()]  # Объединяем фамилию и имя
    users.sort(key=lambda x: x['name'])  # Сортируем по алфавиту по полному имени
    
    for user in users: 
        users_id.append(user['chat_id'])
    
    # Даты для заголовка
    
    dates = []    
    records = {}
    # Проходим по всем таблицам и извлекаем данные
    for table in tables:
        attendance_dict = {}
        table_name = table[0]
        
        if table_name.startswith("lunch_"):
            try:
                date_str = table_name[6:].replace('_', '.')  # Извлекаем дату из имени таблицы
                date = pd.to_datetime(date_str, format="%d.%m.%Y")  # Преобразуем строку в дату

                if start_date <= date <= end_date:
                    dates.append(date.strftime("%d.%m.%Y"))  # Добавляем дату в формате "дд.мм.гггг"
                    cursor.execute(f"SELECT chat_id, will_attend, reason FROM {table_name}")  # Изменено: выбираем chat_id
                    attendance_data = cursor.fetchall()

                    # Создаем словарь для хранения информации о посещении
                    for row in attendance_data: 
                        if row[0] in users_id:  # Изменено: проверяем chat_id
                            user_name = next(user['name'] for user in users if user['chat_id'] == row[0])  # Получаем имя пользователя
                            attendance_dict[user_name] = (row[1], row[2])  # Изменено: используем имя пользователя
                            
            except ValueError:
                continue  # Игнорируем таблицы, которые не являются датами
            finally:
                records[date.strftime("%d.%m.%Y")] = attendance_dict
        
    # Закрытие соединения с базой данных
    conn.close()
    print(records) 
    # Создание DataFrame для отчета
    users_names = [user['name'] for user in users]
    report_df = pd.DataFrame(index=users_names)
    
    # Заполняем DataFrame данными о посещении
    for date in dates:
        report_df[date] = ''  # Инициализируем столбец пустыми значениями
        for key,info in records[date].items():
            will_attend = records[date][key][0]
            reason = records[date][key][1]
            if will_attend == 1:
                        report_df.at[key, date] = '+'
            elif will_attend == 0:
                report_df.at[key, date] = '-'                    
                if reason == 'doc':
                    report_df.at[key, date] = 'З'  # Заявление по болезни
                elif reason == 'ill':
                    report_df.at[key, date] = 'Б'  # Заявление по болезни
    # Сохранение в Excel файл
    output_file = 'attendance_report.xlsx'
    report_df.to_excel(output_file, index=True, sheet_name='Attendance Report')

    # Форматирование ширины столбцов, выравнивание ячеек и границы
    workbook = load_workbook(output_file)
    sheet = workbook.active

    thin_border = Border(left=Side(style='thin'), 
                         right=Side(style='thin'), 
                         top=Side(style='thin'), 
                         bottom=Side(style='thin'))  # Определяем стиль границы

    for i, column in enumerate(sheet.columns):
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
                cell.alignment = Alignment(horizontal='center')  # Выравнивание по центру
                cell.border = thin_border  # Применяем границы к ячейке
            except:
                pass
        
        # Устанавливаем отступы для первого столбца и остальных
        if i == 0:
            adjusted_width = (max_length + 4)  # Отступ +4 для первого столбца
        else:
            adjusted_width = (max_length + 1)  # Отступ +1 для остальных столбцов
        
        sheet.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width

    workbook.save(output_file)  # Сохраняем изменения в файле
    return output_file



def create_keyboard1():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("Да", callback_data="yes"),
        telebot.types.InlineKeyboardButton("Нет", callback_data="no")
    )
    return keyboard

def create_keyboard2():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("Да", callback_data="yes_school"),
        telebot.types.InlineKeyboardButton("Нет", callback_data="no_school")
    )
    return keyboard

def create_keyboard3():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("Больничный", callback_data="ill"),
        telebot.types.InlineKeyboardButton("Заявление", callback_data="doc")
    )
    return keyboard

def create_keyboard_back():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("В главное меню", callback_data="back"))
    return keyboard

def create_keyboard_main():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Проголосовать на завтра", callback_data="vote"))
    keyboard.add(telebot.types.InlineKeyboardButton("Информация о обедах завтра", callback_data="vote_info"))
    keyboard.add(telebot.types.InlineKeyboardButton("Информация о обедах на сегодня", callback_data="vote_info_today"))
    return keyboard

def create_keyboard_phone():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = telebot.types.KeyboardButton(text="Отправить контакт", request_contact=True)
    keyboard.add(button_phone)
    return keyboard

def create_keyboard_priv():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)    
    keyboard.add(telebot.types.KeyboardButton(text="Да"))
    keyboard.add(telebot.types.KeyboardButton(text="Нет"))
    return keyboard

def create_keyboard_reg1():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Зарегестрироваться", callback_data="reg"))
    return keyboard

def create_keyboard_accept_reject_block(chat_id):
    
    callback_data_accept = f'accept${chat_id}'
    callback_data_reject = f'reject${chat_id}'
    callback_data_block = f'block${chat_id}'
    callback_data_accept_teacher = f'accept_teacher${chat_id}'
    
    accept_button = telebot.types.InlineKeyboardButton(text='Принять', callback_data=callback_data_accept)
    reject_button = telebot.types.InlineKeyboardButton(text='Отклонить', callback_data=callback_data_reject)
    block_button = telebot.types.InlineKeyboardButton(text='Заблокировать', callback_data=callback_data_block)
    accept_teacher_button = telebot.types.InlineKeyboardButton(text='Принять как учителя', callback_data=callback_data_accept_teacher)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(accept_button)
    keyboard.add(reject_button)
    keyboard.add(block_button)
    keyboard.add(accept_teacher_button)

    return keyboard

def create_keyboard_reg_check():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Изменить", callback_data="edit"))
    keyboard.add(telebot.types.InlineKeyboardButton("Подтвердить", callback_data="accept"))
    return keyboard

def create_keyboard_main_teacher():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Получить данные по обедам на завтра", callback_data="get_lunch_info_teacher"))
    keyboard.add(telebot.types.InlineKeyboardButton("Получить отчет", callback_data="get_report"))
    return keyboard

def create_keyboard_classes_report(): 
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT class FROM classes""")
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    print (classes)
    for cl in classes: 
        keyboard.add(telebot.types.InlineKeyboardButton(text=f"{cl[0]}", callback_data=f"class_report${cl[0]}"))
    
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    tz = pytz.timezone('Asia/Yekaterinburg')
    tomorrow = datetime.now(tz) + timedelta(days=1)
    date = tomorrow.strftime("%d.%m")
    
    
    create_table(date)
    if db_check_id(message.chat.id) and db_check_status_pupil(message.chat.id):
        bot.send_message(
            message.chat.id,
            f"Добрый день, {message.chat.first_name}! Выберите действие:",
            reply_markup=create_keyboard_main()
        )
    elif db_check_id(message.chat.id) and db_check_status_teacher(message.chat.id):
        bot.send_message(
            message.chat.id,
            f"Добрый день, {message.chat.first_name} вы приняты в базу данных как учитель! Выберите действие:",
            reply_markup=create_keyboard_main_teacher()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Добрый день, {message.chat.first_name}! Для исползования бота, вам необходимо зарегестирвоваться",
            reply_markup=create_keyboard_reg1()
        )

# Обработчик callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    tz = pytz.timezone('Asia/Yekaterinburg')
    tomorrow = datetime.now(tz) + timedelta(days=1)
    date = tomorrow.strftime("%d.%m")
    year = tomorrow.strftime("%Y")
    table_name = f"lunch_{date.replace('.', '_')}_{year}"

    if not db_check_id(call.message.chat.id) :
        if call.data == "reg":
            if check_blocked_user(call.message.chat.id):
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"Вы заблокированы, обратитесь к администратору",)
            elif not check_blocked_user(call.message.chat.id):
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"Введите ваше имя")               
          
                bot.register_next_step_handler(call.message, get_name)  

        elif call.data == "edit":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Введите ваше имя",
                
            )
            bot.register_next_step_handler(call.message, get_name)
        
        elif call.data == "accept":
            winfo = get_waitlist_info(call.message.chat.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Ожидайте, подтверждение. Как только администратор подтвердит ваш запрос, вы получите доступ к боту."
            )
            admin_bot.send_message(
                ADMIN_CHAT_ID,
                f"""Новый запрос на регистрацию
Имя: {winfo[0]}
Фамилия: {winfo[1]}
Класс: {winfo[2]}
Телефон: {winfo[3]}
Имя пользователя: {winfo[6]}
Льготник: {'Да' if winfo[7] else 'Нет' }""",
                reply_markup=create_keyboard_accept_reject_block(call.message.chat.id)
            )
        
        else:             
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Добрый день, {call.message.chat.first_name}! Для исползования бота, вам необходимо зарегестирвоваться",
                reply_markup=create_keyboard_reg1()
            )
            
    elif db_check_status_teacher(call.message.chat.id) and db_check_id(call.message.chat.id):
        if call.data == "get_lunch_info_teacher":
            lunch_info = db_get_lunch_info_teacher(table_name=table_name)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            text=f"Обеды {date}\n{lunch_info}",
            reply_markup=create_keyboard_back()
        )
        elif call.data == "back":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Добрый день, {call.message.chat.first_name}, вы числитесь в базе данных как учитель! Выберите действие:",
                reply_markup=create_keyboard_main_teacher()
            )
        elif call.data == "get_report":
            bot.edit_message_text(chat_id = call.message.chat.id,
                                message_id = call.message.id,
                                text = "Выберите класс для отчета",
                                reply_markup = create_keyboard_classes_report())
            

        elif call.data.startswith('class_report$'):
            grade = call.data.split('$')[1]
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id = call.message.id,
                             text=f"Введите промежуток времени для отчета {grade} через тире например (09.01.2025-09.04.2025)")
            bot.register_next_step_handler(call.message, get_report, grade)

            
   
    elif db_check_id(call.message.chat.id) and db_check_status_pupil(call.message.chat.id):
        
        if call.data == "yes":
            add_lunch_record(
                table_name,
                call.message.chat.id,
                True
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Данные успешно отправлены!",
                reply_markup=create_keyboard_back()
            )

        elif call.data == "vote":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Обеды {date}",
                reply_markup=create_keyboard1()
            )

        elif call.data == "vote_info":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=get_lunch_info(call.message.chat.id),
                reply_markup=create_keyboard_back()
            )

        elif call.data == "vote_info_today":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=get_lunch_info(call.message.chat.id, today=True),
                reply_markup=create_keyboard_back()
            )

        elif call.data == "no":
            add_lunch_record(
                table_name,
                call.message.chat.id,
                False,
                None
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Вы будете завтра в школе?",
                reply_markup=create_keyboard2()
            )

        elif call.data == "yes_school":
            add_lunch_record(
                table_name,
                call.message.chat.id,
                False,
                True
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Данные успешно отправлены!",
                reply_markup=create_keyboard_back()
            )

        elif call.data == "no_school":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Причина отсутствия в школе?",
                reply_markup=create_keyboard3()
            )

        elif call.data == "ill":
            add_lunch_record(
                table_name,
                call.message.chat.id,
                False,
                False,
                "ill"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Данные успешно отправлены!",
                reply_markup=create_keyboard_back()
            )

        elif call.data == "doc":
            add_lunch_record(
                table_name,
                call.message.chat.id,
                False,
                False,
                "doc"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Данные успешно отправлены!",
                reply_markup=create_keyboard_back()
            )

        elif call.data == "back":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Добрый день, {call.message.chat.first_name}! Выберите действие:",
                reply_markup=create_keyboard_main()
            )

    bot.answer_callback_query(call.id)

###регистрация
def get_name(message):
    name = message.text
    print(name)
    add_user_waitlist(message.chat.id, 'chat_id', message.chat.id)
    add_user_waitlist(name, 'first_name', message.chat.id)
    if message.chat.username is not None:
        username = f"@{message.chat.username}"
        add_user_waitlist(username, 'user_name', message.chat.id)
        bot.send_message(
            message.chat.id,  
            'Введите вашу фамилию', 
        )
        bot.register_next_step_handler(message, get_last_name)        
    else:
        bot.send_message(
            chat_id = message.chat.id,
            text = 'Для регистрации требуется username вашего телеграм аккаунта. Пожайлутста укажите его в своем профиле телеграм и попробуйте зарегестрироваться заново',
            reply_markup = create_keyboard_reg1()
        )
   
def get_last_name(message):
    last_name = message.text
    print(last_name)
    add_user_waitlist(last_name, 'last_name', message.chat.id)
    bot.send_message(
        message.chat.id, 
        'Ведите ваш класс', 
        
    )
    bot.register_next_step_handler(message, get_grade)

def get_grade(message):
    grade = message.text.upper()
    
    
    add_user_waitlist(grade, 'grade', message.chat.id)
    bot.send_message(
        chat_id = message.chat.id,
        text = 'Вы являетесь льготником?',
        reply_markup = create_keyboard_priv()
    )
    bot.register_next_step_handler(message, get_priv)

def get_priv(message):
    priv = 0
    if message.text == 'Да':
        priv = 1 
    elif message.text == 'Нет':
        priv == 0
    add_user_waitlist(priv,'privil', message.chat.id)


    remove_keyboard = telebot.types.ReplyKeyboardRemove()
    temp_msg = bot.send_message(message.chat.id, "Данные успешно сохранены!", reply_markup=remove_keyboard)
    bot.delete_message(message.chat.id, temp_msg.message_id)  
    
    bot.send_message(
        message.chat.id, 
        'Нажмите кнопку ниже чтобы указать свой номер телефона', 
        reply_markup=create_keyboard_phone()
    )
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    
    phone = message.contact.phone_number
    
    
    
    add_user_waitlist(phone, 'phone', message.chat.id) 
    
    remove_keyboard = telebot.types.ReplyKeyboardRemove()
    temp_msg = bot.send_message(message.chat.id, "Данные успешно сохранены!", reply_markup=remove_keyboard)
    winfo = get_waitlist_info(message.chat.id)    
    print(winfo)
    bot.send_message(
        message.chat.id,
        f"""Проверьте введенные даныные и нажмите кнопку 'Подтвердить', если все верно.
Ваши данные:
Имя: {winfo[0]}
Фамилия: {winfo[1]}
Класс: {winfo[2]}
Телефон: {winfo[3]}
Имя пользователя: {winfo[6]}
Льготник: {'Да' if winfo[7] else 'Нет' }
        """,
        reply_markup=create_keyboard_reg_check()
    )


###создаие отчета
def get_report(message, grade): 
    dates = message.text.split('-')
    generate_attendance_report(dates[0], dates[1], grade)    
    with open('attendance_report.xlsx', 'rb') as file:
        bot.send_document(
            chat_id=message.chat.id,
            document=file
        )
    bot.send_message(chat_id=message.chat.id,
                     text=f"Добрый день, {message.chat.first_name}, вы числитесь в базе данных как учитель! Выберите действие:",
                     reply_markup=create_keyboard_main_teacher())
    





if __name__ == '__main__':

    bot.polling(none_stop=True)