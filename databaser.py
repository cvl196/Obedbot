import sqlite3
from sqlite3 import Error
from datetime import datetime
import pandas as pd
import os


def create_connection():
    """
    Создает подключение к базе данных SQLite
    Возвращает объект соединения или None при ошибке
    """
    try:
        conn = sqlite3.connect('lunch_database.db')
        return conn
    except Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None

def add_record_for_date(date, chat_id, name, will_eat, will_attend=None, reason=None):



    """
    Добавляет запись в таблицу для указанной даты
    
    Параметры:
    date (str): Дата в формате 'dd.mm.yyyy'
    chat_id (int): ID чата пользователя
    name (str): Имя пользователя
    will_eat (bool): Будет ли обедать
    will_attend (bool): Будет ли в школе
    reason (str): Причина отсутствия
    """
    
    # Преобразование строковых значений в булевы
    if isinstance(will_eat, str):
        will_eat = will_eat.lower() == "да"
    if isinstance(will_attend, str) and will_attend is not None:
        will_attend = will_attend.lower() == "да"
    
    # Если человек будет обедать, то он точно будет в школе
    if will_eat:
        will_attend = True
        reason = None
    
    # Разбиваем дату на компоненты
    day, month, year = date.split('.')
    # Создаем название таблицы из даты
    table_name = f"lunch_{day}_{month}_{year}"
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Создаем таблицу, если она не существует
            cursor.execute(f''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}' ''')
            if cursor.fetchone()[0] == 0:
                cursor.execute(f'''
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        will_eat BOOLEAN NOT NULL,
                        will_attend BOOLEAN,
                        reason TEXT
                    )
                ''')
            
            # Проверяем, существует ли уже запись для этого chat_id
            cursor.execute(f"SELECT id FROM {table_name} WHERE chat_id = ?", (chat_id,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Обновляем существующую запись
                cursor.execute(f'''
                    UPDATE {table_name}
                    SET will_eat = ?, will_attend = ?, reason = ?
                    WHERE chat_id = ?
                ''', (will_eat, will_attend, reason, chat_id))
            else:
                # Создаем новую запись
                cursor.execute(f'''
                    INSERT INTO {table_name} (chat_id, name, will_eat, will_attend, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (chat_id, name, will_eat, will_attend, reason))
            
            conn.commit()
            return True
            
        except Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
            return False
        finally:
            conn.close()
    return False

def add_user(first_name, last_name, grade, phone, chat_id, status,user_name):
    """
    Добавляет нового пользователя или обновляет существующего в таблице users
    
    Args:
        first_name (str): Имя пользователя
        last_name (str): Фамилия пользователя  
        grade (str): Класс
        phone (str): Номер телефона
        chat_id (int): ID чата Telegram
        status (str): Статус пользователя (pupil/teacher/admin)
    
    Returns:
        bool: True если пользователь успешно добавлен/обновлен, False если произошла ошибка
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            
            
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    grade TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    status TEXT NOT NULL,
                    user_name TEXT NOT NULL
                )
            ''')
            
            # Проверяем существует ли пользователь с таким chat_id
            cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
            if cursor.fetchone() is not None:
                # Обновляем данные существующего пользователя
                cursor.execute('''
                    UPDATE users 
                    SET first_name = ?, last_name = ?, grade = ?, phone = ?, status = ?, user_name = ?
                    WHERE chat_id = ?
                ''', (first_name, last_name, grade, phone, status, user_name, chat_id))
                print(f"Данные пользователя с chat_id {chat_id} обновлены")
            else:
                # Добавляем нового пользователя
                cursor.execute('''
                    INSERT INTO users (chat_id, first_name, last_name, grade, phone, status, user_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, first_name, last_name, grade, phone, status, user_name))
                print(f"Пользователь {first_name} {last_name} успешно добавлен")
            
            conn.commit()
            return True
            
        except Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
            return False
        finally:
            conn.close()
    return False

def add_user_waitlist(first_name, last_name, grade, phone, chat_id, status,user_name):
    """
    Добавляет нового пользователя или обновляет существующего в таблице users
    
    Args:
        first_name (str): Имя пользователя
        last_name (str): Фамилия пользователя  
        grade (str): Класс
        phone (str): Номер телефона
        chat_id (int): ID чата Telegram
        status (str): Статус пользователя (pupil/teacher/admin)
    
    Returns:
        bool: True если пользователь успешно добавлен/обновлен, False если произошла ошибка
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Проверяем существование таблицы users
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS users_waitlist (                   
                    chat_id INTEGER UNIQUE NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    grade TEXT,
                    phone TEXT,
                    status TEXT,
                    user_name TEXT
                    
                )
            ''')
            
            # Проверяем существует ли пользователь с таким chat_id
            cursor.execute("SELECT chat_id FROM users_waitlist WHERE chat_id = ?", (chat_id,))
            if cursor.fetchone() is not None:
                # Обновляем данные существующего пользователя
                cursor.execute('''
                    UPDATE users_waitlist 
                    SET first_name = ?, last_name = ?, grade = ?, phone = ?, status = ?, user_name = ?
                    WHERE chat_id = ?
                ''', (first_name, last_name, grade, phone, status, user_name, chat_id))
                print(f"Данные пользователя с chat_id {chat_id} обновлены")
            else:
                # Добавляем нового пользователя
                cursor.execute('''
                    INSERT INTO users_waitlist (chat_id, first_name, last_name, grade, phone, status, user_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, first_name, last_name, grade, phone, status, user_name))
                print(f"Пользователь {first_name} {last_name} успешно добавлен")
            
            conn.commit()
            return True
            
        except Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
            return False
        finally:
            conn.close()
    return False

def add_user_waitlist_2(new_value, column_name, chat_id):
    """
    Обновляет указанный столбец для пользователя в таблице users_waitlist
    
    Args:
        new_value: Новое значение для столбца
        column_name (str): Название столбца для обновления
        chat_id (int): ID чата пользователя
    
    Returns:
        bool: True если обновление успешно, False если произошла ошибка
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Получаем информацию о столбцах таблицы
            cursor.execute("PRAGMA table_info(users_waitlist)")
            columns = [info[1] for info in cursor.fetchall()]
            
            # Проверяем существует ли указанный столбец
            if column_name not in columns:
                print(f"Столбец {column_name} не существует в таблице")
                return False
                
            # Обновляем значение в указанном столбце
            cursor.execute(f'''
                UPDATE users_waitlist 
                SET {column_name} = ?
                WHERE chat_id = ?
            ''', (new_value, chat_id))
            
            conn.commit()
            
            # Проверяем, было ли обновление успешным
            if cursor.rowcount > 0:
                print(f"Значение в столбце {column_name} обновлено для chat_id {chat_id}")
                return True
            else:
                print(f"Пользователь с chat_id {chat_id} не найден")
                return False
                
        except Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
            return False
        finally:
            conn.close()
    return False

def drop_table(table_name):
    """
    Удаляет таблицу из базы данных по её названию
    
    Args:
        table_name (str): Название таблицы для удаления
    
    Returns:
        bool: True если таблица успешно удалена, False если произошла ошибка или таблица не существует
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Проверяем существование таблицы
            cursor.execute(f''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', (table_name,))
            if cursor.fetchone()[0] == 0:
                print(f"Таблица {table_name} не существует")
                return False
            
            # Удаляем таблицу
            cursor.execute(f'DROP TABLE {table_name}')
            conn.commit()
            print(f"Таблица {table_name} успешно удалена")
            return True
            
        except Error as e:
            print(f"Ошибка при удалении таблицы: {e}")
            return False
        finally:
            conn.close()
    return False

def create_table(table_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                    
                    chat_id INTEGER NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    grade TEXT, 
                    phone INTEGER,                     
                    status TEXT,
                    user_name TEXT,
                    privil BOOLEAN,

                    CONSTRAINT class_fk FOREIGN KEY (grade) REFERENCES classes (class)
                   )""" )
    conn.commit()
    conn.close()

def delete_user(chat_id):
    """Удаляет пользователя из таблицы users по chat_id."""
    conn = create_connection()
    cursor = conn.cursor()

    try:
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

def generate_attendance_report(start_date_str, end_date_str):
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
    cursor.execute("SELECT first_name, chat_id FROM users;")

    users_id = []
    users = [{'name' : row[0], 'chat_id' : row[1]} for row in cursor.fetchall()]
    
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
                    cursor.execute(f"SELECT name, will_attend,reason, chat_id  FROM {table_name}")
                    attendance_data = cursor.fetchall()

                    # Создаем словарь для хранения информации о посещении
                    
                    for row in attendance_data: 
                        if row[3] in users_id: 
                            attendance_dict[row[0]] = (row[1], row[2], row[3])                   

            except ValueError:
                continue  # Игнорируем таблицы, которые не являются датами
            finally:
                # print(date, records)  # Удалено
                records[date.strftime("%d.%m.%Y")] = attendance_dict
        
    # Закрытие соединения с базой данных
    conn.close()
    print(records) 
    # Создание DataFrame для отчета
    users_names = [user['name']for user in users]
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

    return output_file

def clean_table(table_name):
    """
    Очищает все записи в указанной таблице.
    
    Args:
        table_name (str): Название таблицы для очистки.
    
    Returns:
        bool: True если таблица успешно очищена, False если произошла ошибка.
    """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Удаляем все записи из таблицы
            cursor.execute(f"DELETE FROM {table_name}")
            conn.commit()
            print(f"Все записи из таблицы {table_name} успешно очищены.")
            return True
            
        except Error as e:
            print(f"Ошибка при очистке таблицы: {e}")
            return False
        finally:
            conn.close()
    return False

def add_column(table_name, new_column, type): 
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Добавляем новый столбец в указанную таблицу
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {new_column} {type}')
            conn.commit()
            print(f"Столбец {new_column} успешно добавлен в таблицу {table_name}.")
            return True
        except Error as e:
            print(f"Ошибка при добавлении столбца: {e}")
            return False
        finally:
            conn.close()
    return False
drop_table('lunch_14_01_2025')