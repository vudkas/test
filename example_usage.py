#!/usr/bin/env python3
"""
Shopify Checkout Example - For Educational Purposes Only

This script demonstrates how to use the improved_shopify_checkout module
for educational purposes, authorized testing, or merchant-approved use only.

IMPORTANT: Automated checkout scripts may violate Shopify's Terms of Service.
Only use this code in compliance with all applicable terms, laws, and regulations.
"""

import argparse
import json
import logging
from improved_shopify_checkout import process_checkout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('example_usage')

def main():
    """
    Parse command line arguments and run the checkout process.
    """
    parser = argparse.ArgumentParser(description='Shopify Checkout Example (Educational Use Only)')
    
    parser.add_argument('--url', required=True, help='Product URL')
    parser.add_argument('--proxy', help='Proxy in format ip:port or ip:port:user:pass')
    
    # Optional payment details (only include if explicitly testing payment flow)
    parser.add_argument('--cc', help='Credit card number')
    parser.add_argument('--month', help='Expiration month (2 digits)')
    parser.add_argument('--year', help='Expiration year (2 or 4 digits)')
    parser.add_argument('--cvv', help='Card verification value')
    
    args = parser.parse_args()
    
    # Display warning about terms of service
    print("\n" + "="*80)
    print("WARNING: This script is for EDUCATIONAL PURPOSES ONLY")
    print("Automated checkout scripts may violate Shopify's Terms of Service.")
    print("Only use this code in compliance with all applicable terms, laws, and regulations.")
    print("="*80 + "\n")
    
    # Check if payment details are provided
    if any([args.cc, args.month, args.year, args.cvv]) and not all([args.cc, args.month, args.year, args.cvv]):
        logger.error("If providing payment details, all fields (cc, month, year, cvv) are required")
        return
    
    # Process checkout
    logger.info(f"Starting checkout process for: {args.url}")
    
    result = process_checkout(
        product_url=args.url,
        cc=args.cc,
        month=args.month,
        year=args.year,
        cvv=args.cvv,
        custom_proxy=args.proxy
    )
    
    # Display result
    print("\nCheckout Result:")
    print(json.dumps(result, indent=2))
    
    # Provide guidance based on result
    if result.get('status'):
        if 'checkout_url' in result and not args.cc:
            print("\nSuccessfully added to cart and obtained checkout URL.")
            print("To complete checkout manually, visit:")
            print(result['checkout_url'])
        else:
            print("\nCheckout completed successfully!")
    else:
        print(f"\nCheckout failed: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()