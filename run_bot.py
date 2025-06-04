#!/usr/bin/env python3
"""
Shopify Checkout Bot Runner

This script provides a command-line interface to run the Shopify checkout bot.
"""

import argparse
import json
from colorama import Fore, Style, init
from shopify_bot import ShopifyBot

# Initialize colorama for colored terminal output
init(autoreset=True)

def main():
    """
    Parse command line arguments and run the Shopify checkout bot.
    """
    parser = argparse.ArgumentParser(description='Shopify Checkout Bot')
    parser.add_argument('--url', required=True, help='Product URL')
    parser.add_argument('--proxy', help='Proxy in format ip:port or ip:port:user:pass')
    
    # Optional payment details
    parser.add_argument('--cc', help='Credit card number')
    parser.add_argument('--month', help='Expiration month (2 digits)')
    parser.add_argument('--year', help='Expiration year (2 or 4 digits)')
    parser.add_argument('--cvv', help='Card verification value')
    
    args = parser.parse_args()
    
    # Check if payment details are provided
    if any([args.cc, args.month, args.year, args.cvv]) and not all([args.cc, args.month, args.year, args.cvv]):
        print(f"{Fore.RED}If providing payment details, all fields (cc, month, year, cvv) are required{Style.RESET_ALL}")
        return
    
    # Print banner
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🛒 Shopify Checkout Bot{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    # Initialize the bot
    bot = ShopifyBot(custom_proxy=args.proxy)
    
    # Run the checkout process
    result = bot.run_checkout(
        product_url=args.url,
        cc=args.cc,
        month=args.month,
        year=args.year,
        cvv=args.cvv
    )
    
    # Display result
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Checkout Result:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    if result.get('status'):
        if 'checkout_url' in result and not args.cc:
            print(f"\n{Fore.GREEN}✅ Successfully added to cart and obtained checkout URL.{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}Product: {result.get('product')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Variant: {result.get('variant')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Price: {result.get('price')}{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}To complete checkout manually, visit:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{result['checkout_url']}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✅ Checkout completed successfully!{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}Product: {result.get('product')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Variant: {result.get('variant')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Price: {result.get('price')}{Style.RESET_ALL}")
            if 'order_id' in result:
                print(f"{Fore.YELLOW}Order ID: {result.get('order_id')}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Checkout failed: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")
        if 'result' in result:
            print(f"{Fore.RED}Result: {result.get('result')}{Style.RESET_ALL}")
        if 'product' in result:
            print(f"\n{Fore.YELLOW}Product: {result.get('product')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Variant: {result.get('variant')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Price: {result.get('price')}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()