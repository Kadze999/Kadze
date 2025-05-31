import telebot
import json
import os
import re
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '7958245884:AAHIsfXGoCQBvWNfmY0IN2hCb7N2bOsYrWE'

bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'users.json'

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/start'), KeyboardButton('/info'), KeyboardButton('/play'), KeyboardButton('/top'))
    return kb

def play_again_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Играть ещё'))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = str(message.chat.id)
    if chat_id not in user_data:
        user_data[chat_id] = {'step': 'name', 'score': 0}
        save_data()
    else:
        user_data[chat_id]['step'] = 'name'
        save_data()
    bot.send_message(chat_id,
                     "Привет! Как тебя зовут?\n\n"
                     "Введите имя (первая буква — буква, остальные любые символы).",
                     reply_markup=main_keyboard())

@bot.message_handler(commands=['info'])
def cmd_info(message):
    chat_id = str(message.chat.id)
    data = user_data.get(chat_id)
    if not data or 'name' not in data or 'age' not in data:
        bot.send_message(chat_id, "Сначала представься, пожалуйста, с помощью /start", reply_markup=main_keyboard())
        return
    text = f"Имя: {data['name']}\nВозраст: {data['age']}\nОчки: {data.get('score', 0)}"
    bot.send_message(chat_id, text, reply_markup=main_keyboard())

@bot.message_handler(commands=['play'])
def cmd_play(message):
    chat_id = str(message.chat.id)
    data = user_data.get(chat_id)
    if not data or 'name' not in data or 'age' not in data:
        bot.send_message(chat_id, "Сначала представься, пожалуйста, с помощью /start", reply_markup=main_keyboard())
        return
    if 'game' in data and data['game'].get('active'):
        bot.send_message(chat_id, "Игра уже идёт! Попробуй угадать число.", reply_markup=main_keyboard())
        return
    data['game'] = {
        'active': True,
        'number': random.randint(1, 20)
    }
    save_data()
    bot.send_message(chat_id, "Я загадал число от 1 до 20. Попробуй угадать!", reply_markup=main_keyboard())

@bot.message_handler(commands=['top'])
def cmd_top(message):
    chat_id = str(message.chat.id)
    if not user_data:
        bot.send_message(chat_id, "Пока нет данных об игроках.", reply_markup=main_keyboard())
        return
    
    scores = []
    for user_id, data in user_data.items():
        if 'name' in data and 'score' in data:
            scores.append((data['name'], data['score']))
    
    if not scores:
        bot.send_message(chat_id, "Пока нет игроков с очками.", reply_markup=main_keyboard())
        return
    
    scores.sort(key=lambda x: x[1], reverse=True)
    top_scores = scores[:50]
    
    text = "🏆 Топ игроков:\n\n"
    for i, (name, score) in enumerate(top_scores, start=1):
        text += f"{i}. {name} — {score} очков\n"
    
    bot.send_message(chat_id, text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    data = user_data.get(chat_id)

    if not data:
        user_data[chat_id] = {'step': 'name', 'score': 0}
        save_data()
        bot.send_message(chat_id, "Привет! Как тебя зовут?", reply_markup=main_keyboard())
        return

    step = data.get('step')

    if step == 'name':
        if not text:
            bot.send_message(chat_id, "Имя не может быть пустым. Попробуй ещё раз.", reply_markup=main_keyboard())
            return
        if not re.match(r'^[A-Za-zА-Яа-яЁё]', text):
            bot.send_message(chat_id, "Имя должно начинаться с буквы. Попробуй ещё раз.", reply_markup=main_keyboard())
            return
        if len(text) < 2 or len(text) > 30:
            bot.send_message(chat_id, "Имя должно быть от 2 до 30 символов.", reply_markup=main_keyboard())
            return
        data['name'] = text
        data['step'] = 'age'
        save_data()
        bot.send_message(chat_id, f"Приятно познакомиться, {text}! Сколько тебе лет? (от 2 до 100)", reply_markup=main_keyboard())
        return

    if step == 'age':
        if not text.isdigit():
            bot.send_message(chat_id, "Пожалуйста, введи возраст числом.", reply_markup=main_keyboard())
            return
        age = int(text)
        if age < 2 or age > 100:
            bot.send_message(chat_id, "Возраст должен быть от 2 до 100 лет. Введи, пожалуйста, правильный возраст.", reply_markup=main_keyboard())
            return
        data['age'] = age
        data['step'] = None
        save_data()
        bot.send_message(chat_id, f"Отлично, {data['name']}! Теперь ты можешь начать игру с командой /play", reply_markup=main_keyboard())
        return

    if data.get('game', {}).get('active'):
        if text.lower() == 'играть ещё':
            data['game'] = {
                'active': True,
                'number': random.randint(1, 20)
            }
            save_data()
            bot.send_message(chat_id, "Я загадал новое число от 1 до 20. Попробуй угадать!", reply_markup=main_keyboard())
            return

        if not text.isdigit():
            bot.send_message(chat_id, "Пожалуйста, введи число от 1 до 20.", reply_markup=main_keyboard())
            return
        guess = int(text)
        if guess < 1 or guess > 20:
            bot.send_message(chat_id, "Число должно быть от 1 до 20.", reply_markup=main_keyboard())
            return
        secret = data['game']['number']
        if guess == secret:
            data['score'] = data.get('score', 0) + 1
            data['game']['active'] = False
            save_data()
            bot.send_message(chat_id, f"Поздравляю! Ты угадал число {secret}.\nТвои очки: {data['score']}", reply_markup=play_again_keyboard())
        elif guess < secret:
            bot.send_message(chat_id, "Загаданное число больше. Попробуй ещё раз.", reply_markup=main_keyboard())
        else:
            bot.send_message(chat_id, "Загаданное число меньше. Попробуй ещё раз.", reply_markup=main_keyboard())
        return

    if text.lower() == 'играть ещё':
        data['game'] = {
            'active': True,
            'number': random.randint(1, 20)
        }
        save_data()
        bot.send_message(chat_id, "Я загадал число от 1 до 20. Попробуй угадать!", reply_markup=main_keyboard())
        return

    bot.send_message(chat_id, "Используй команды /start, /info, /play, /top или кнопку 'Играть ещё'.", reply_markup=main_keyboard())

bot.polling()
