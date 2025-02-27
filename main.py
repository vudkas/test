# main.py
import logging
from config import ENV
from src.pythonfixer import register_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="bot.log",
    filemode="a"
)
logger = logging.getLogger()

myenv = ENV()
bot = myenv.connect()
register_handler(bot)

if __name__ == "__main__":
    try:
        bot.start(bot_token=myenv.token)
        logger.info("Bot started correctly")
        print("Bot started correctly")
        bot.run_until_disconnected()
    except Exception as e:
        logger.exception("Error starting bot: %s", e)
        print("Error starting bot:", e)
