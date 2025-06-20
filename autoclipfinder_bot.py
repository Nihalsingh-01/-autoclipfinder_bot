# autoclipfinder_bot.py
import telebot
import datetime
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "PASTE_YOUR_BOTFATHER_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    status TEXT,
    expiry DATE
)
""")
conn.commit()

UPI_IDS = ["9905401362@ibl", "9905401362@ybl", "9905401362@axl"]
QR_IMAGE_URL = "https://example.com/your_qr_image.png"
ADMIN_USERNAME = "@YOUR_TELEGRAM_USERNAME"

language_map = {
    "India": {
        "Uttar Pradesh": "सर्वश्रेष्ठ पल",
        "Maharashtra": "सर्वोत्तम क्षण",
        "Tamil Nadu": "சிறந்த தருணம்",
        "West Bengal": "সেরা মুহূর্ত",
        "Default": "सर्वश्रेष्ठ पल"
    },
    "USA": {"Default": "Best Moment"},
    "France": {"Default": "Meilleur Moment"},
    "Germany": {"Default": "Bester Moment"},
    "Japan": {"Default": "最高の瞬間"},
    "Default": {"Default": "Best Moment"}
}

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    countries = ["India", "USA", "France", "Germany", "Japan"]
    for c in countries:
        markup.add(InlineKeyboardButton(text=c, callback_data=f"country_{c}"))
    bot.send_message(message.chat.id, "🌐 Please select your country:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country(call):
    country = call.data.split("_")[1]
    user_data[call.from_user.id] = {"country": country}

    if country == "India":
        markup = InlineKeyboardMarkup()
        states = ["Uttar Pradesh", "Maharashtra", "Tamil Nadu", "West Bengal"]
        for s in states:
            markup.add(InlineKeyboardButton(text=s, callback_data=f"region_{s}"))
        bot.edit_message_text("🇮🇳 Select your state:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        user_data[call.from_user.id]["region"] = "Default"
        bot.send_message(call.message.chat.id, "✅ Setup done! Now send a YouTube link to start.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("region_"))
def handle_region(call):
    region = call.data.split("_")[1]
    user_data[call.from_user.id]["region"] = region
    bot.send_message(call.message.chat.id, "✅ Setup done! Now send a YouTube link to start.")

@bot.message_handler(commands=['verify'])
def verify(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Format: /verify TXN_ID Your_Name")
        return
    txn, name = parts[1], " ".join(parts[2:])
    msg = f"🧾 Payment verification request:\n👤 @{message.from_user.username}\n💳 TXN ID: {txn}\n🙋‍♂️ Name: {name}\n\n✅ To approve: /approve @{message.from_user.username}"
    bot.send_message(ADMIN_USERNAME, msg)
    bot.reply_to(message, "✅ Your TXN has been submitted for review.")

@bot.message_handler(commands=['approve'])
def approve(message):
    parts = message.text.split()
    if len(parts) != 2:
        return
    username = parts[1].lstrip("@")
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE users SET status = ?, expiry = ? WHERE username = ?", ("premium", expiry_date, username))
    else:
        cursor.execute("INSERT INTO users (username, status, expiry) VALUES (?, ?, ?)", (username, "premium", expiry_date))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ @{username} is now approved until {expiry_date}.")

bot.polling()