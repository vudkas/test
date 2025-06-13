#!/usr/bin/env python3
"""
Test script for the enhanced Shopify bot
"""

import sys
import logging
from enhanced_shopify_bot import EnhancedShopifyBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_enhanced_bot')

def test_product_fetch(url, custom_proxy=None):
    """Test fetching product information"""
    logger.info(f"Testing product fetch from {url}")
    
    # Initialize the bot
    bot = EnhancedShopifyBot(custom_proxy=custom_proxy)
    
    # Fetch product information
    product_info = bot.get_product_info(url)
    
    if product_info:
        logger.info("Product information fetched successfully:")
        logger.info(f"Title: {product_info.get('title')}")
        logger.info(f"Price: {product_info.get('price')}")
        logger.info(f"Variant ID: {product_info.get('variant_id')}")
        logger.info(f"Domain: {product_info.get('domain')}")
        return True
    else:
        logger.error("Failed to fetch product information")
        return False

def test_add_to_cart(url, custom_proxy=None):
    """Test adding a product to cart"""
    logger.info(f"Testing add to cart for {url}")
    
    # Initialize the bot
    bot = EnhancedShopifyBot(custom_proxy=custom_proxy)
    
    # Fetch product information
    product_info = bot.get_product_info(url)
    
    if not product_info:
        logger.error("Failed to fetch product information")
        return False
    
    # Add to cart
    result = bot.add_to_cart(product_info)
    
    if result:
        logger.info("Product added to cart successfully")
        return True
    else:
        logger.error("Failed to add product to cart")
        return False

def test_checkout_url(url, custom_proxy=None):
    """Test getting checkout URL"""
    logger.info(f"Testing checkout URL for {url}")
    
    # Initialize the bot
    bot = EnhancedShopifyBot(custom_proxy=custom_proxy)
    
    # Fetch product information
    product_info = bot.get_product_info(url)
    
    if not product_info:
        logger.error("Failed to fetch product information")
        return False
    
    # Add to cart
    add_result = bot.add_to_cart(product_info)
    
    if not add_result:
        logger.error("Failed to add product to cart")
        return False
    
    # Get checkout URL
    checkout_url = bot.get_checkout_url(product_info)
    
    if checkout_url:
        logger.info(f"Checkout URL: {checkout_url}")
        return True
    else:
        logger.error("Failed to get checkout URL")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the enhanced Shopify bot')
    parser.add_argument('--url', default='https://klaritylifestyle.com/products/power-stripe-skirt', help='URL of the product page')
    parser.add_argument('--proxy', help='Proxy to use (format: ip:port:user:pass)')
    parser.add_argument('--test', choices=['product', 'cart', 'checkout', 'all'], default='all', help='Test to run')
    
    args = parser.parse_args()
    
    url = args.url
    custom_proxy = args.proxy
    test_type = args.test
    
    if test_type == 'product' or test_type == 'all':
        test_product_fetch(url, custom_proxy)
    
    if test_type == 'cart' or test_type == 'all':
        test_add_to_cart(url, custom_proxy)
    
    if test_type == 'checkout' or test_type == 'all':
        test_checkout_url(url, custom_proxy)

if __name__ == '__main__':
    main()