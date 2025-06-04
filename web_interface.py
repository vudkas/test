#!/usr/bin/env python3
"""
Shopify Checkout Bot Web Interface

This script provides a web interface to run the Shopify checkout bot.
"""

from flask import Flask, render_template, request, jsonify
import json
import threading
import time
from shopify_bot import ShopifyBot

app = Flask(__name__)

# Store bot instances and results
bots = {}
results = {}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('bot.html')

@app.route('/api/checkout', methods=['POST'])
def checkout():
    """Start a checkout process"""
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'error': 'Product URL is required'}), 400
        
    # Generate a unique ID for this checkout
    checkout_id = str(int(time.time()))
    
    # Get parameters
    product_url = data.get('url')
    proxy = data.get('proxy')
    cc = data.get('cc')
    month = data.get('month')
    year = data.get('year')
    cvv = data.get('cvv')
    
    # Check if payment details are provided
    if any([cc, month, year, cvv]) and not all([cc, month, year, cvv]):
        return jsonify({'error': 'If providing payment details, all fields (cc, month, year, cvv) are required'}), 400
    
    # Initialize the bot
    bot = ShopifyBot(custom_proxy=proxy)
    bots[checkout_id] = bot
    
    # Start the checkout process in a separate thread
    def run_checkout():
        result = bot.run_checkout(
            product_url=product_url,
            cc=cc,
            month=month,
            year=year,
            cvv=cvv
        )
        results[checkout_id] = result
        
    thread = threading.Thread(target=run_checkout)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'checkout_id': checkout_id,
        'message': 'Checkout process started',
        'status': 'running'
    })

@app.route('/api/status/<checkout_id>', methods=['GET'])
def status(checkout_id):
    """Get the status of a checkout process"""
    if checkout_id not in bots:
        return jsonify({'error': 'Invalid checkout ID'}), 404
        
    if checkout_id in results:
        return jsonify({
            'checkout_id': checkout_id,
            'status': 'completed',
            'result': results[checkout_id]
        })
    else:
        return jsonify({
            'checkout_id': checkout_id,
            'status': 'running'
        })

@app.route('/api/cancel/<checkout_id>', methods=['POST'])
def cancel(checkout_id):
    """Cancel a checkout process"""
    if checkout_id not in bots:
        return jsonify({'error': 'Invalid checkout ID'}), 404
        
    # We can't actually cancel the thread, but we can remove it from our tracking
    if checkout_id in bots:
        del bots[checkout_id]
    if checkout_id in results:
        del results[checkout_id]
        
    return jsonify({
        'checkout_id': checkout_id,
        'status': 'cancelled'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12000, debug=True)