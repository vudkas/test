import telebot
from flask import Flask, request
import os

token = "6928284331:AAF7BI7UJqkfN7BZ2lIsIbwRpuh1gsE_cbI"
bot = telebot.TeleBot(token)

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello, I'm a bot!")

@app.route('/')
def home():
    return "Bot is up and running!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 400

def set_webhook():
    webhook_url = "https://test-w95v.onrender.com/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)