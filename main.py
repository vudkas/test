import telebot
from flask import Flask, request
import os

# Telegram Bot Token
token = "6928284331:AAF7BI7UJqkfN7BZ2lIsIbwRpuh1gsE_cbI"
bot = telebot.TeleBot(token)

# Initialize Flask app
app = Flask(__name__)

# Define a command handler for /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello, I'm a bot!")

# Home route to verify the bot is running
@app.route('/')
def home():
    return "Bot is up and running!", 200

# Webhook route for Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Process the incoming update
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 400

# Set the webhook URL
def set_webhook():
    # The full webhook URL (include `/webhook`)
    webhook_url = "https://test-w95v.onrender.com/webhook"
    bot.remove_webhook()  # Remove any existing webhook
    bot.set_webhook(url=webhook_url)  # Set the new webhook

# Main entry point
if __name__ == "__main__":
    # Set the webhook when the app starts
    set_webhook()
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)