import telebot
import sqlite3
from datetime import datetime
import time
import requests

TOKEN = '8992217710:AAHgdwlL6Fbvuc3J4RuvhHNO5j9n3Vuo9sY'
bot = telebot.TeleBot(TOKEN)
WEB_APP_URL = 'https://democasino.github.io/democasino/?v=18'

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('players.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            wins INTEGER DEFAULT 0,
            games INTEGER DEFAULT 0,
            last_win TEXT
        )
    ''')
    conn.commit()
    return conn

db_conn = init_db()

def add_win(user_id, username):
    conn = db_conn
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO players (user_id, username, wins, games, last_win) 
        VALUES (?, ?, 1, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET 
            wins = wins + 1,
            games = games + 1,
            username = ?,
            last_win = ?
    ''', (user_id, username, datetime.now().isoformat(), username, datetime.now().isoformat()))
    conn.commit()

def add_game(user_id):
    conn = db_conn
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET games = games + 1 WHERE user_id = ?', (user_id,))
    conn.commit()

def get_top_players(limit=10):
    conn = db_conn
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, wins, games FROM players 
        ORDER BY wins DESC, games ASC 
        LIMIT ?
    ''', (limit,))
    return cursor.fetchall()

def get_player_stats(user_id):
    conn = db_conn
    cursor = conn.cursor()
    cursor.execute('SELECT wins, games FROM players WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return {'wins': result[0], 'games': result[1]}
    return {'wins': 0, 'games': 0}

# ===== КЛАВИАТУРА =====
def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🎰 Игра")
    btn2 = telebot.types.KeyboardButton("🏆 Рейтинг")
    markup.add(btn1, btn2)
    return markup

# ===== ОБРАБОТЧИКИ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Аноним"
    add_game(user_id)
    stats = get_player_stats(user_id)
    
    bot.send_message(
        message.chat.id,
        f"🎲 *NFT CASINO*\n━━━━━━━━━━━━━━━\n\n"
        f"Привет, {username}! 👋\n"
        f"🏅 Твои победы: *{stats['wins']}*\n"
        f"🎮 Сыграно игр: *{stats['games']}*\n\n"
        f"Выбери действие в меню ниже 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['top'])
def top_command(message):
    top_players = get_top_players(10)
    if not top_players:
        bot.send_message(
            message.chat.id,
            "🏆 *ТОП-10 ИГРОКОВ*\n━━━━━━━━━━━━━━━\n\nПока никто не играл! Будь первым! 🚀",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return
    
    text = "🏆 *ТОП-10 ИГРОКОВ*\n━━━━━━━━━━━━━━━\n\n"
    for i, (username, wins, games) in enumerate(top_players, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{username} — *{wins} побед* ({games} игр)\n"
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@bot.message_handler(commands=['win'])
def handle_win(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Аноним"
    add_win(user_id, username)
    stats = get_player_stats(user_id)
    bot.send_message(
        message.chat.id,
        f"🎉 *Победа записана!*\n🏅 Всего побед: *{stats['wins']}*\n🎮 Сыграно игр: *{stats['games']}*",
        parse_mode="Markdown"
    )

# ===== КНОПКИ МЕНЮ =====
@bot.message_handler(func=lambda message: message.text == "🎰 Игра")
def open_game(message):
    markup = telebot.types.InlineKeyboardMarkup()
    web_app_btn = telebot.types.InlineKeyboardButton(
        text="🎰 Открыть рулетку",
        web_app=telebot.types.WebAppInfo(url=WEB_APP_URL)
    )
    markup.add(web_app_btn)
    bot.send_message(
        message.chat.id,
        "Нажми на кнопку, чтобы открыть игру 👇",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🏆 Рейтинг")
def show_rating(message):
    top_command(message)

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("🤖 Бот запускается...")
    print("👤 @democasinotgBot")
    
    try:
        requests.get(f'https://api.telegram.org/bot{TOKEN}/deleteWebhook', timeout=5)
        print("✅ Webhook отключён")
    except:
        print("⚠️ Не удалось отключить webhook")
    
    while True:
        try:
            print("🔄 Подключаюсь к Telegram...")
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)
