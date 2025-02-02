import telebot
import datetime
from datetime import date, timedelta

# Списки дат в формате (месяц, день)
birthdays = [
    (1, 1), (1, 7), (1, 18),
    (2, 1), (2, 10),
    (3, 27),
    (4, 9), (4, 16), (4, 21), (4, 25),
    (5, 12), (5, 14), (5, 25), (5, 27), (5, 28),
    (6, 9),
    (7, 27),
    (8, 17), (8, 19), (8, 21),
    (9, 27), (9, 30),
    (10, 1), (10, 11), (10, 24),
    (11, 25)
]

holidays = [
    (12, 29), (12, 30), (12, 31),
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
    (2, 24),
    (3, 24), (3, 25), (3, 26), (3, 27), (3, 28), (3, 29), (3, 30),
    (1, 30),  # Исправлено с сентября (9) на январь (1)
    (9, 30)
]

TOKEN = '7373139324:AAGI6MHFU1IXfVs3elE9CM-6gJrbVvvpNBs'
CHAT_ID = -1001826080759

bot = telebot.TeleBot(TOKEN)

def check_date(target_date):
    """Проверяет дату в ежегодных событиях"""
    month_day = (target_date.month, target_date.day)
    return {
        'is_birthday': month_day in birthdays,
        'is_holiday': month_day in holidays,
        'is_weekend': target_date.weekday() == 6  # 6 = воскресенье
    }

# Получаем завтрашнюю дату
tomorrow = date.today() + timedelta(days=1)
date_info = check_date(tomorrow)

# Форматируем дату для вывода
formatted_date = tomorrow.strftime('%d.%m')

if date_info['is_birthday']:
    bot.send_poll(
        chat_id=CHAT_ID,
        question=f"🎉 Обед {formatted_date} 🎉",
        options=['🎉 Буду есть 🎉', '🎉 Не буду 🎉'],
        is_anonymous=False
    )
elif not date_info['is_holiday'] and not date_info['is_weekend']:
    bot.send_poll(
        chat_id=CHAT_ID,
        question=f"Обед {formatted_date}",
        options=['Буду есть', 'Не буду'],
        is_anonymous=False
    )

