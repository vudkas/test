# src/handlers.py
import logging
import asyncio
import re
from telethon import events, Button
from src.services.python_service import PythonService
from config import ENV

logger = logging.getLogger(__name__)
env = ENV()

# Command handlers
async def start_command(event):
    """Handle the /start command"""
    user = await event.get_sender()
    username = user.username or user.first_name or "User"
    
    welcome_message = (
        f"👋 Welcome, {username}!\n\n"
        f"I'm a Python code optimizer bot. Send me your Python code, and I'll analyze and optimize it.\n\n"
        f"✅ Just paste your code directly or use triple backticks\n"
        f"✅ I'll provide optimization recommendations and explanations\n"
        f"✅ Get detailed feedback on potential improvements"
    )
    
    buttons = [
        [Button.url("📣 Join Our Channel", env.channel_link)],
        [Button.text("ℹ️ About", single_use=True), Button.text("❓ Help", single_use=True)]
    ]
    
    await event.reply(welcome_message, buttons=buttons)
    logger.info(f"Sent welcome message to user {username} (ID: {user.id})")

async def help_command(event):
    """Handle the /help command"""
    help_message = (
        "🔍 **How to use this bot:**\n\n"
        "1️⃣ Send your Python code directly in the chat\n"
        "2️⃣ Or use triple backticks for better formatting:\n"
        "```python\n"
        "your_code_here\n"
        "```\n\n"
        "3️⃣ Wait for the analysis to complete\n"
        "4️⃣ Get optimized code and detailed explanations\n\n"
        "📚 **Available commands:**\n"
        "/start - Restart the bot\n"
        "/help - Show this help message\n"
        "/about - Information about the bot"
    )
    
    await event.reply(help_message)
    logger.info(f"Sent help message to user {event.sender_id}")

async def about_command(event):
    """Handle the /about command"""
    about_message = (
        "🤖 **Python Optimizer Bot**\n\n"
        "This bot uses advanced AI to analyze your Python code and suggest optimizations, "
        "security improvements, and best practices.\n\n"
        "Powered by CloudDefense.AI technology.\n\n"
        "Version: 2.1.0\n"
        "Updated: February 2025"
    )
    
    buttons = [[Button.url("📣 Join Our Channel", env.channel_link)]]
    await event.reply(about_message, buttons=buttons)
    logger.info(f"Sent about message to user {event.sender_id}")

async def button_handler(event):
    """Handle button clicks"""
    if event.data == b"Help":
        await help_command(event)
    elif event.data == b"About":
        await about_command(event)

# Main message handler
async def message_handler(event):
    """Process incoming messages with code"""
    if event.message.text.startswith('/'):
        return  # Skip command messages
    
    # Get user information
    sender = await event.get_sender()
    username = sender.username or sender.first_name or "User"
    logger.info(f"Processing code request from {username} (ID: {sender.id})")
    
    # Extract code from message
    text = event.message.text.strip()
    if not text:
        await event.reply("Please send some Python code to optimize.")
        return
    
    # Extract code from triple backticks if present
    if text.startswith("```") and text.endswith("```"):
        # Check if language is specified (like ```python)
        first_line = text.split('\n', 1)[0]
        if len(first_line) > 3 and not first_line[3:].strip() == "python":
            # If language is specified but not python, notify user
            if len(first_line) > 3:
                await event.reply("I can only optimize Python code. Please send Python code.")
                return
        
        # Remove triple backticks and language specification if present
        code = text.split('\n', 1)
        if len(code) > 1:
            code = code[1]
        else:
            code = ""
        
        if code.endswith("```"):
            code = code[:-3].strip()
    else:
        code = text
    
    # Initial response
    waiting_message = (
        f"⏳ Processing your code, {username}...\n\n"
        f"I'll analyze it for optimization opportunities, security improvements, and best practices."
    )
    
    # Add progress indicator buttons
    buttons = [[Button.url("📣 Join Our Channel", env.channel_link)]]
    processing_msg = await event.reply(waiting_message, buttons=buttons)
    
    # Update the message with progress indicators
    for i in range(3):
        await asyncio.sleep(1)
        await processing_msg.edit(
            waiting_message + f"\n\nAnalyzing{'.' * (i + 1)}",
            buttons=buttons
        )
    
    # Process the code
    try:
        python_service = PythonService()
        result = await python_service.optimize_code(code)
        
        if result["status"] == "success":
            data = result["data"]
            optimized_code = data.get("optimized_code", "")
            explanation = data.get("explanation", "")
            
            # Clean up the response
            clean_explanation = re.sub(r'<[^>]*>', '', explanation).strip()
            clean_code = re.sub(r'</?code>', '', optimized_code).strip()
            
            # Format the response
            response = (
                f"✅ **Code Optimization Complete**\n\n"
                f"**Improvements:**\n{clean_explanation}\n\n"
                f"**Optimized Code:**\n```python\n{clean_code}\n```"
            )
            
            # Check if message is too long
            if len(response) > 4000:
                # Truncate the code part if needed
                summary = (
                    f"✅ **Code Optimization Complete**\n\n"
                    f"**Improvements:**\n{clean_explanation}\n\n"
                )
                
                remaining_length = 4000 - len(summary) - 20  # 20 chars for markdown
                truncated_code = clean_code[:remaining_length] + "...\n[Code truncated due to length]"
                response = f"{summary}**Optimized Code:**\n```python\n{truncated_code}\n```"
            
            await processing_msg.edit(response, buttons=buttons)
            logger.info(f"Successfully delivered optimization results to {username}")
        else:
            error_message = (
                f"❌ **Error Processing Code**\n\n"
                f"I couldn't optimize your code. Error: {result.get('message', 'Unknown error')}\n\n"
                f"Please check your code and try again."
            )
            await processing_msg.edit(error_message, buttons=buttons)
            logger.error(f"Error processing code for {username}: {result.get('message')}")
    
    except Exception as e:
        error_message = f"❌ **Unexpected Error**\n\nAn error occurred while processing your code."
        await processing_msg.edit(error_message, buttons=buttons)
        logger.exception(f"Exception processing message from {username}: {e}")

def register_all_handlers(bot):
    """Register all event handlers"""
    # Command handlers
    bot.add_event_handler(start_command, events.NewMessage(pattern='/start'))
    bot.add_event_handler(help_command, events.NewMessage(pattern='/help'))
    bot.add_event_handler(about_command, events.NewMessage(pattern='/about'))
    
    # Button click handler
    bot.add_event_handler(button_handler, events.CallbackQuery())
    
    # General message handler for code processing
    bot.add_event_handler(message_handler, events.NewMessage())
    
    logger.info("All handlers registered successfully")