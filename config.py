# config.py
from dotenv import load_dotenv
import os
from telethon import TelegramClient

class ENV:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("TOKEN")
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
    def connect(self):
        return TelegramClient("pybot", self.api_id, self.api_hash)
