# main.py
import logging
import sys
from datetime import datetime
from config import ENV
from src.handlers import register_all_handlers

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing bot...")
    
    # Load environment variables
    try:
        myenv = ENV()
        if not myenv.is_configured():
            logger.error("Bot configuration is incomplete. Please check your .env file.")
            return
    except Exception as e:
        logger.critical(f"Failed to load environment variables: {e}")
        return
    
    # Connect to Telegram
    try:
        logger.info("Connecting to Telegram...")
        bot = myenv.connect()
        logger.info("Connection established successfully")
    except Exception as e:
        logger.critical(f"Failed to connect to Telegram: {e}")
        return
    
    # Register all handlers
    register_all_handlers(bot)
    
    # Start the bot
    try:
        logger.info("Starting bot...")
        bot.start(bot_token=myenv.token)
        logger.info("Bot started successfully")
        print("✅ Bot is now running. Press Ctrl+C to stop.")
        
        # Run the bot until disconnected
        bot.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Error running bot: {e}")
    finally:
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    main()