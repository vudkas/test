import telebot
from flask import Flask, request
import os

token = "6928284331:AAF7BI7UJqkfN7BZ2lIsIbwRpuh1gsE_cbI"
bot = telebot.TeleBot(token)

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

def set_webhook():
    url = "https://test-w95v.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=url)

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=5000)
