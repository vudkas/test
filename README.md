A Telegram bot that analyzes and optimizes Python code using the CloudDefense.AI API.

## Features

- Python code analysis and optimization
- Security vulnerability detection
- Best practices recommendations
- Explanation of recommended changes

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the required environment variables:
   ```
   TOKEN=your_telegram_bot_token
   API_ID=your_telegram_api_id
   API_HASH=your_telegram_api_hash
   SESSION_NAME=pybot
   CHANNEL_LINK=https://t.me/YourChannelLink
   MAX_RETRIES=3
   RETRY_DELAY=1
   API_URL=https://api-pseo.clouddefense.ai:8000/code-clarity/fix-vulnerability
   ```
4. Run the bot: `python main.py`

## Usage

1. Start a chat with the bot on Telegram
2. Send Python code directly or using triple backticks
3. Receive optimized code and explanations

## Commands

- `/start` - Start the bot
- `/help` - Show help information
- `/about` - Show information about the bot