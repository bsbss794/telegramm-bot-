# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:36863686@localhost:5432/studia_of_beautiful_api?sslmode=disable"

# Импортируй свою функцию подключения к БД
# from database import get_db_connection

def get_db_connection():
    """Создаёт и возвращает подключение к БД"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

def send_reminder(appointment_id, slot_id, start_time):
    """Отправляет напоминание клиенту"""
    try:
        from bot import bot  # импортируем бота из основного файла

        time_str = start_time.strftime("%d.%m.%Y в %H:%M")
        text = f"🔔 Напоминаем! У вас запись на {time_str}."
        db = get_db_connection()
        if db is None:
            print("error connecting to database")
            return
        bot.send_message(appointment_id, text)

        # Отмечаем, что напоминание отправлено
        mark_reminder_sent(slot_id)
        return True
    except Exception as e:
        print(f"Ошибка отправки напоминания: {e}")
        return False


def mark_reminder_sent(appointment_id):
    """Отмечает в БД, что напоминание отправлено"""
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE slots1 SET reminder_sent = TRUE WHERE id = %s", (appointment_id,))
    db.commit()
    db.close()
    pass  # замени на свой код


def check_upcoming_appointments():
    """Проверяет записи, которые начнутся через час"""
    now = datetime.now()
    target_time = now + timedelta(hours=1)
    print(f"проверка! сейчас: {now} ищу: {target_time}") 

    db = get_db_connection()
    if db is None:
        print("error connecting to database")
        return
    cursor = db.cursor()
    cursor.execute("""
            SELECT id, client, start_time FROM slots1
            WHERE status = 'booked'
            AND reminder_sent = FALSE
            AND start_time BETWEEN %s AND %s
        """, (now, target_time))
    appointments = cursor.fetchall()
    print(f"проверка! найдено: {Len(appointments)}") 

    for app in appointments:
        cursor = db.cursor()
        cursor.execute("SELECT user_id FROM clients1 WHERE id = %s", (app[1],))
        appointments_id = cursor.fetchall()
        if not appointments_id:
            print("client nor found")
            return
        for id in appointments_id:
            print(f": {id[0]}: {app[2]}")
            send_reminder(id[0], app[0], app[2])
    db.close()


def start_scheduler():
    """Запускает фоновый планировщик"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_appointments, 'interval', minutes=1)
    scheduler.start()
    print("✅ Планировщик напоминаний запущен!")
    return scheduler
