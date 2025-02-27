# pythonfixer.py
import logging
import requests
import asyncio
import re
import time
from telethon import events, Button

logger = logging.getLogger(__name__)

def pythonchk(code):
    logger.info("Calling external API to check code")
    url = "https://api-pseo.clouddefense.ai:8000/code-clarity/fix-vulnerability"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
        "Origin": "https://www.clouddefense.ai",
        "Referer": "https://www.clouddefense.ai/"
    }
    data = {"code": code, "lang": "python"}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data)
            logger.info("API response status: %s", response.status_code)
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get("status") == "success":
                    return json_response
                else:
                    logger.error("API returned error: %s", json_response)
                    return {"status": "error", "message": json_response.get("message", "Unknown error")}
            elif response.status_code == 500:
                logger.warning("API error 500 on attempt %d", attempt + 1)
                if attempt < max_retries - 1:
                    time.sleep(1)  # wait 1 second before retrying
                    continue
                else:
                    return {"status": "error", "message": "API error: 500"}
            else:
                logger.error("API error: Non-200 response: %s", response.status_code)
                return {"status": "error", "message": "API error: " + str(response.status_code)}
        except Exception as e:
            logger.exception("Exception in pythonchk: %s", e)
            return {"status": "error", "message": str(e)}

def register_handler(bot):
    @bot.on(events.NewMessage)
    async def handler(event):
        logger.info("Received new message from %s", event.sender_id)
        text = event.message.text.strip()
        if not text:
            return

        # Handle /start command without calling the API.
        if text.startswith("/start"):
            welcome_message = "Welcome! Send your Python code to get it optimized."
            button = [[Button.url("Join Our Channel", "https://t.me/YourChannelLink")]]
            await event.reply(welcome_message, buttons=button)
            logger.info("Processed /start command")
            return

        # Get sender information.
        sender = await event.get_sender()
        username = sender.username if sender.username else "User"

        # If code is wrapped in triple backticks, remove them.
        if text.startswith("```") and text.endswith("```"):
            code = text[3:-3].strip()
        else:
            code = text

        # Send initial reply message with wait information.
        initial_message = (f"Hi {username}, please wait while we process your code. "
                           "Estimated wait time: 10 seconds.")
        button = [[Button.url("Join Our Channel", "https://t.me/YourChannelLink")]]
        reply_msg = await event.reply(initial_message, buttons=button)
        logger.info("Sent initial wait message to %s", username)

        # Wait 10 seconds before processing the code.
        await asyncio.sleep(10)
        logger.info("Processing code after wait for %s", username)

        result = pythonchk(code)
        if result.get("status") == "success":
            data = result.get("data", {})
            optimized_code = data.get("optimized_code", "")
            explanation = data.get("explanation", "")
            # Remove HTML tags from explanation and set custom format.
            clean_explanation = re.sub(r'<[^>]*>', '', explanation).strip()
            custom_explanation = f"Optimized Code Explanation:\n{clean_explanation}"
            # Remove <code> tags from optimized_code.
            clean_code = re.sub(r'</?code>', '', optimized_code).strip()
            reply_text = f"{custom_explanation}\n\n```python\n{clean_code}\n```"
            if len(reply_text) > 4000:
                reply_text = f"{custom_explanation}\n\n```python\n{clean_code[:4000]}\n```"
                button = [[Button.url("Join Our Channel", "https://t.me/YourChannelLink")]]
            # Edit the initial message with the fixed code.
            await reply_msg.edit(reply_text, buttons=button)
            logger.info("Edited message with optimized code for %s", username)
        else:
            error_message = f"Error processing code: {result.get('message')}"
            await reply_msg.edit(error_message, buttons=button)
            logger.error("Error processing code for %s: %s", username, result.get("message"))
