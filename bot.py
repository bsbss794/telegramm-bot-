import telebot
import requests
from datetime import datetime
from telebot import types
from scheduler import start_scheduler

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
SERVER_URL = "https://server-for-biautiful-bot-production.up.railway.app/"
ADMIN_ID = os.getenv("ADMIN_ID")


@bot.message_handler(commands=['start'])  # стартовая команда
def start(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton('➕ добавить слот')
        btn2 = types.KeyboardButton('💯 посмотреть отзыв(один)')
        btn3 = types.KeyboardButton('💯 посмотреть отзывы')
        btn6 = types.KeyboardButton('🕠 посмотреть все слоты')
        btn5 = types.KeyboardButton('👤 посмотреть клиента')
        btn4 = types.KeyboardButton('👤 посмотреть клиентов')
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

        bot.reply_to(message, "🛠 Админ-панель:", reply_markup=markup)
        return
    user_id = message.from_user.id
    username = message.from_user.username
    response = requests.get(f"{SERVER_URL}/new_client?user_id={user_id}&username={username}")
    if response.status_code == 200:

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton('📅 Записаться')
        btn2 = types.KeyboardButton('⭐ Оставить отзыв')
        btn3 = types.KeyboardButton('⭐ мой отзыв')
        btn4 = types.KeyboardButton('📞 Контакты')
        markup.add(btn1, btn2, btn3, btn4)

        bot.reply_to(message, "Выберите действие:", reply_markup=markup)
    else:
        bot.reply_to(message, "error")

@bot.message_handler(func=lambda message: message.text == '📞 Контакты')
def contact(message):
    text = "👤 Контакты:\n"
    text += "📞 номер телефона: +79999999999\n"
    text += "🏩адрес: ул.пушкина д.9\n"

    bot.reply_to(message, text)

@bot.message_handler(commands=['slot'])
def free_slot(message):
    try:
        result = []
        response = requests.get(f"{SERVER_URL}/free_slot")
        if response.status_code == 200:
            result = response.json()
            if not result:
                bot.reply_to(message, "свободного времени пока нет")
                return
        else:
            bot.reply_to(message, "ошибка сервера")
            return
        text = "свободное время:\n"
        for r in result:
            text += f"------------------------------\n№ id: {r['id']}\n🕟время начала(дата время): {r['start_time']}\n🕟время окончания(дата время): {r['end_time']}\n ------------------------------\n"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(func=lambda message: message.text == '🕠 посмотреть все слоты')
def get_slots(message):
    try:
        chat_id = message.chat.id
        if chat_id != ADMIN_ID:
            bot.reply_to(message, "вы не являетесь администратором")
            return
        result = []
        response = requests.get(f"{SERVER_URL}/slot")
        if response.status_code == 200:
            result = response.json()
            if not result:
                bot.reply_to(message, "времени пока нет")
                return
        else:
            bot.reply_to(message, "ошибка сервера")
            return
        text = "свободное время:\n"
        for r in result:
            text += f"------------------------------\n№ id: {r['id']}\n🕟время начала(дата время): {r['start_time']}\n🕟время окончания(дата время): {r['end_time']}\n статус: {r['status']}\n------------------------------\n"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, e)


user_data = {}  # Хранит промежуточные данные пользователя

@bot.message_handler(func=lambda message: message.text == '⭐ Оставить отзыв')
def start_review(message):
    user_data[message.chat.id] = {}
    bot.reply_to(message, "📝 Введите имя операции (или напишите '-' для пропуска):")
    bot.register_next_step_handler(message, get_master_name)

def get_master_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['operation'] = message.text if message.text != '-' else 'Не указан'
    bot.reply_to(message, "✍️ Напишите текст отзыва:")
    bot.register_next_step_handler(message, get_review_text)

def get_review_text(message):
    chat_id = message.chat.id
    user_data[chat_id]['text'] = message.text
    bot.reply_to(message, "⭐ Оцените работу от 1 до 5:")
    bot.register_next_step_handler(message, get_rating)

def get_rating(message):
    chat_id = message.chat.id
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError
    except:
        bot.reply_to(message, "❌ Ошибка! Введите число от 1 до 5:")
        bot.register_next_step_handler(message, get_rating)
        return

    user_data[chat_id]['rating'] = rating

    # Теперь у нас есть все данные
    data = user_data[chat_id]


    response = requests.get(f"{SERVER_URL}/new_rewiew?username={chat_id}&text={data['text']}&rating={data['rating']}&operation={data['operation']}")
    if response.status_code == 200:
        bot.reply_to(message,
                     f"✅ Спасибо за отзыв!\n\n👤 операция: {data['operation']}\n📝 Текст: {data['text']}\n⭐ Оценка: {data['rating']}")
        notify_admin(f"📢 Новый отзыв!\nКлиент: {message.from_user.username}\n👤 операция: {data['operation']}\n📝 Текст: {data['text']}\n⭐ Оценка: {data['rating']}")
    else:
        bot.reply_to(message, "ошибка сервера. скорее всего у вас уже был написан отзыв")
        return

    del user_data[chat_id]  # Очищаем данные пользователя

@bot.message_handler(func=lambda message: message.text == '➕ добавить слот')
def start_slot(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.reply_to(message, "вы не являетесь администратором")
        return
    user_data[message.chat.id] = {}
    bot.reply_to(message, "📝 Введите время начала:")
    bot.register_next_step_handler(message, get_master_name_slot)

def get_master_name_slot(message):
    chat_id = message.chat.id
    user_data[chat_id]['start_time'] = message.text if message.text != '-' else 'Не указан'
    bot.reply_to(message, "введите время окончания:")
    bot.register_next_step_handler(message, get_review_text_slot)

def get_review_text_slot(message):
    chat_id = message.chat.id
    user_data[chat_id]['end_time'] = message.text
    bot.reply_to(message, "введите статус:")
    bot.register_next_step_handler(message, get_rating_slot)

def get_rating_slot(message):
    chat_id = message.chat.id

    user_data[chat_id]['status'] = message.text

    # Теперь у нас есть все данные
    data = user_data[chat_id]


    response = requests.get(f"{SERVER_URL}/new_slot?start_time={data['start_time']}&end_time={data['end_time']}&status={data['status']}")
    if response.status_code == 200:
        bot.reply_to(message,
                     f"время добавлено!\n🕟начало - {data['start_time']}\n🕟конец - {data['end_time']}\nстатус - {data['status']}\n")
    else:
        bot.reply_to(message, "ошибка сервера")
        return

    del user_data[chat_id]  # Очищаем данные пользователя

@bot.message_handler(func=lambda message: message.text == '💯 посмотреть отзывы')
def get_rewiews(message):
    try:
        result = []
        response = requests.get(f"{SERVER_URL}/rewiews")
        if response.status_code == 200:
            result = response.json()
            if not result:
                bot.reply_to(message, "отзывов пока нет")
                return
        else:
            bot.reply_to(message, "ошибка сервера")
            return
        text = "отзывы:\n"
        for r in result:
            text += f"--------------------\n№ id: {r['ID']}\n 👤username - {r['Username']}\n👤 операция: {r['Operation']}\n📝 Текст: {r['Text']}\n⭐ Оценка: {r['Rating']}\n🕟 Создан - {r['CreatedAt']}\n--------------------\n"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(func=lambda message: message.text == '👤 посмотреть клиентов')
def get_clients(message):
    try:
        chat_id = message.chat.id
        if chat_id != ADMIN_ID:
            bot.reply_to(message, "вы не являетесь администратором")
            return
        result = []
        response = requests.get(f"{SERVER_URL}/clients")
        if response.status_code == 200:
            result = response.json()
            if not result:
                bot.reply_to(message, "клиентов пока нет")
                return
        else:
            bot.reply_to(message, "ошибка сервера")
            return
        text = "клиенты:\n"
        for r in result:
            text += f"---------------------\n№ id: {r['ID']}\n👤 юзернейм - {r['Username']}\n👤 user_id - {r['User_id']}\n🕟 создан - {r['CreatedAt']}\n---------------------\n"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(func=lambda message: message.text == '👤 посмотреть клиента')
def start_client(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.reply_to(message, "вы не являетесь администратором")
        return
    user_data[message.chat.id] = {}
    bot.reply_to(message, "📝 Введите id клиента")
    bot.register_next_step_handler(message, get_master_name_client)

def get_master_name_client(message):
    chat_id = message.chat.id
    user_data[chat_id]['id'] = message.text if message.text != '-' else 'Не указан'
    data = user_data[chat_id]
    result = {}
    response = requests.get(
        f"{SERVER_URL}/client?id={data['id']}")
    if response.status_code == 200:
        data = response.json()
        result = data[0]
        if not result:
            bot.reply_to(message, "клиент не найден")
            return
    else:
        bot.reply_to(message, "ошибка сервера")
        return
    text = "клиент:\n"
    text += f"---------------------\n№ id: {result['ID']}\n👤 юзернейм - {result['Username']}\n👤 user_id - {result['User_id']}\n🕟 создан - {result['CreatedAt']}\n---------------------\n"
    bot.reply_to(message, text)
    del user_data[chat_id]  # Очищаем данные пользователя

@bot.message_handler(func=lambda message: message.text == '💯 посмотреть отзыв(один)')
def start_rewiew(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.reply_to(message, "вы не являетесь администратором")
    user_data[message.chat.id] = {}
    bot.reply_to(message, "📝 Введите id отзыва")
    bot.register_next_step_handler(message, get_master_name_rewiew)

def get_master_name_rewiew(message):
    chat_id = message.chat.id
    user_data[chat_id]['id'] = message.text if message.text != '-' else 'Не указан'
    data = user_data[chat_id]
    result = {}
    response = requests.get(
        f"{SERVER_URL}/rewiew?id={data['id']}")
    if response.status_code == 200:
        data = response.json()
        result = data[0]
        if not result:
            bot.reply_to(message, "клиент не найден")
            return
    else:
        bot.reply_to(message, "ошибка сервера")
        return
    text = "клиент:\n"
    text += f"№ id: {result['ID']}\n 👤username - {result['Username']}\n👤 операция: {result['Operation']}\n📝 Текст: {result['Text']}\n⭐ Оценка: {result['Rating']}\n🕟 Создан - {result['CreatedAt']}\n"
    bot.reply_to(message, text)
    del user_data[chat_id]  # Очищаем данные пользователя

@bot.message_handler(func=lambda message: message.text == '📅 Записаться')
def start_boocked(message):
    free_slot(message)
    user_data[message.chat.id] = {}
    bot.reply_to(message, "📝 Введите id слота")
    bot.register_next_step_handler(message, get_master_name_boocked)

def get_master_name_boocked(message):
    chat_id = message.chat.id
    user_data[chat_id]['id'] = message.text if message.text != '-' else 'Не указан'
    data = user_data[chat_id]

    response = requests.get(
        f"{SERVER_URL}/slot_boocked?client_id={chat_id}&slot_id={data['id']}")
    if response.status_code == 200:
        bot.reply_to(message,
                     f"вы записались на слот: {data['id']}")
        notify_admin(f"📢 новая запись!\n 👤клиент - {chat_id}\n слот - {data['id']}")
    else:
        bot.reply_to(message, f"ошибка сервера! возможно вы ввели неверный id: {data['id']}")
        return

    del user_data[chat_id]  # Очищаем данные пользователя

@bot.message_handler(func=lambda message: message.text == '⭐ мой отзыв')
def get_my_rewiew(message):
    try:
        result = []
        response = requests.get(f"{SERVER_URL}/user_get_rewiew?username={message.from_user.id}")
        if response.status_code == 200:
            data = response.json()
            result = data[0]
            if not result:
                bot.reply_to(message, " у вас нет отзыва")
                return
        else:
            bot.reply_to(message, "ошибка сервера")
            return
        text = "отзыв:\n"
        text += f"💬текст: {result['Text']}\n💯оценка: {result['Rating']}\n👤 операция - {result['Operation']}\n"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, e)

def notify_admin(text):
    try:
        bot.send_message(ADMIN_ID, text)
    except Exception as e:
        print(f"Ошибка отправки админу {ADMIN_ID}: {e}")

scheduler = start_scheduler()

if __name__ == '__main__':
    bot.infinity_polling()
