#!/usr/bin/env python3
"""
Test script for direct checkout with a product URL
"""

import sys
import json
import logging
import argparse
from enhanced_shopify_bot_v2 import EnhancedShopifyBotV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("direct_checkout_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_direct_checkout')

def main():
    parser = argparse.ArgumentParser(description='Test direct checkout with a product URL')
    parser.add_argument('--url', required=True, help='Product URL to test')
    parser.add_argument('--card', required=True, help='Card info to test (format: number|month|year|cvv)')
    parser.add_argument('--proxy', help='Proxy to use (format: ip:port:user:pass)')
    parser.add_argument('--output', default='direct_checkout_result.json', help='Output file for results')
    
    args = parser.parse_args()
    
    logger.info(f"Testing direct checkout for product: {args.url}")
    logger.info(f"Using card: {args.card}")
    
    # Parse card info
    cc_number, cc_month, cc_year, cc_cvv = args.card.split('|')
    
    # Initialize the bot
    bot = EnhancedShopifyBotV2(custom_proxy=args.proxy)
    
    # Get product information
    product_info = bot.get_product_info(args.url)
    
    if not product_info:
        logger.error("Failed to get product information")
        result = {
            "success": False,
            "error": "Failed to get product information",
            "url": args.url,
            "card": args.card
        }
    else:
        logger.info(f"Product information: {product_info}")
        
        # Add to cart
        add_result = bot.add_to_cart(product_info)
        
        if not add_result:
            logger.error("Failed to add product to cart")
            result = {
                "success": False,
                "error": "Failed to add product to cart",
                "url": args.url,
                "card": args.card,
                "product_info": product_info
            }
        else:
            logger.info("Successfully added product to cart")
            
            # Get checkout URL
            checkout_url = bot.get_checkout_url(product_info)
            
            if not checkout_url:
                logger.error("Failed to get checkout URL")
                result = {
                    "success": False,
                    "error": "Failed to get checkout URL",
                    "url": args.url,
                    "card": args.card,
                    "product_info": product_info
                }
            else:
                logger.info(f"Checkout URL: {checkout_url}")
                
                # Submit shipping information
                shipping_result = bot.submit_shipping_info()
                
                if not shipping_result:
                    logger.error("Failed to submit shipping information")
                    result = {
                        "success": False,
                        "error": "Failed to submit shipping information",
                        "url": args.url,
                        "card": args.card,
                        "product_info": product_info,
                        "checkout_url": checkout_url
                    }
                else:
                    logger.info("Successfully submitted shipping information")
                    
                    # Select shipping method
                    shipping_method_result = bot.select_shipping_method()
                    
                    if not shipping_method_result:
                        logger.error("Failed to select shipping method")
                        result = {
                            "success": False,
                            "error": "Failed to select shipping method",
                            "url": args.url,
                            "card": args.card,
                            "product_info": product_info,
                            "checkout_url": checkout_url
                        }
                    else:
                        logger.info("Successfully selected shipping method")
                        
                        # Process payment
                        payment_result = bot.process_payment(cc_number, cc_month, cc_year, cc_cvv)
                        
                        if payment_result.get("success", False):
                            logger.info(f"Payment successful! Thank you page: {payment_result.get('thank_you_url')}")
                            result = {
                                "success": True,
                                "url": args.url,
                                "card": args.card,
                                "product_info": product_info,
                                "checkout_url": checkout_url,
                                "payment_result": payment_result,
                                "thank_you_url": payment_result.get("thank_you_url")
                            }
                        else:
                            logger.error(f"Payment failed: {payment_result.get('error')}")
                            result = {
                                "success": False,
                                "error": payment_result.get("error", "Unknown payment error"),
                                "url": args.url,
                                "card": args.card,
                                "product_info": product_info,
                                "checkout_url": checkout_url,
                                "payment_result": payment_result
                            }
    
    # Save the result
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Test complete. Results saved to {args.output}")
    
    # Print summary
    status = "✅ Success" if result.get("success", False) else "❌ Failed"
    error = f" - {result.get('error', '')}" if not result.get("success", False) else ""
    logger.info(f"Summary: {status}{error}")

if __name__ == "__main__":
    main()