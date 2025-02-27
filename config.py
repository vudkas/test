# config.py
import os
import logging
from dotenv import load_dotenv
from telethon import TelegramClient

logger = logging.getLogger(__name__)

class ENV:
    """Handle environment variables and client connections"""
    
    REQUIRED_VARS = ["TOKEN", "API_ID", "API_HASH"]
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get essential credentials
        self.token = os.getenv("TOKEN")
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        
        # Get optional configuration
        self.session_name = os.getenv("SESSION_NAME", "pybot")
        self.channel_link = os.getenv("CHANNEL_LINK", "https://t.me/YourChannelLink")
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "1"))
        self.api_url = os.getenv("API_URL", "https://api-pseo.clouddefense.ai:8000/code-clarity/fix-vulnerability")
        
    def is_configured(self):
        """Check if all required environment variables are set"""
        missing_vars = [var for var in self.REQUIRED_VARS if not getattr(self, var.lower(), None)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def connect(self):
        """Create and return a Telegram client instance"""
        logger.info(f"Creating new client session: {self.session_name}")
        
        # Convert API ID to integer (Telethon requirement)
        try:
            api_id = int(self.api_id)
        except ValueError:
            logger.error("API_ID must be an integer")
            raise ValueError("API_ID must be an integer")
        
        return TelegramClient(self.session_name, api_id, self.api_hash)