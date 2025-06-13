#!/usr/bin/env python3
"""
Automated Shopify Checkout Test Script

This script tests the checkout process on a Shopify site using provided proxies and credit cards.
It attempts to:
1. Visit a product page
2. Add a product to cart
3. Extract session cookies
4. Go to checkout
5. Set shipping/billing address
6. Process payment
7. Check for success or error messages
"""

import sys
import json
import time
import re
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Import ShopifyBot from main.py
from shopify_bot import ShopifyBot

class ShopifyCheckoutTester:
    """
    A class to test the Shopify checkout process with different proxies and credit cards
    """
    
    def __init__(self):
        self.proxies = [
            "193.233.118.40:61234:user552:r7jugq38",
            "134.202.43.145:61234:user401:i5Jp8KCl",
            "46.232.76.52:61234:user564:ZRyvOBsB",
            "94.241.181.71:61234:user1095:7xfdKMGR",
            "88.135.111.38:61234:user2086:ST3SGDXU",
            "159.197.229.219:61234:user219:EniGCswd",
            "159.197.238.51:61234:user_7747e550dc7d:e1ULEKrY",
            "159.197.238.102:61234:user_4653065bc829:JqD6s22J",
            "159.197.238.119:61234:user_580cf90e5f40:Hc3rhpkH",
            "139.190.222.87:61234:user_282a376e0fb7:ftoYN3Pn"
        ]
        
        self.credit_cards = [
            {"number": "5577557193296184", "month": "05", "year": "2026", "cvv": "620"},
            {"number": "5395937416657109", "month": "05", "year": "2026", "cvv": "364"},
            {"number": "4895040589255203", "month": "12", "year": "2027", "cvv": "410"},
            {"number": "5509890034510718", "month": "06", "year": "2028", "cvv": "788"}
        ]
        
        # Test URLs - add more Shopify sites as needed
        self.test_urls = [
            "https://klaritylifestyle.com/products/power-stripe-skirt",
            "https://www.allbirds.com/products/mens-wool-runner-up-mizzles-natural-black",
            "https://www.gymshark.com/products/gymshark-arrival-5-shorts-black-ss21"
        ]
        
    def generate_random_user_data(self):
        """Generate random user data for shipping/billing"""
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller"]
        
        # Generate a random email
        email = f"{random.choice(first_names).lower()}.{random.choice(last_names).lower()}{random.randint(1, 999)}@example.com"
        
        return {
            "email": email,
            "first_name": random.choice(first_names),
            "last_name": random.choice(last_names),
            "address1": f"{random.randint(1, 999)} Main St",
            "address2": f"Apt {random.randint(1, 100)}",
            "city": "New York",
            "state": "NY",
            "zip": f"1000{random.randint(1, 9)}",
            "country": "United States",
            "phone": f"212{random.randint(1000000, 9999999)}"
        }
        
    def test_checkout(self, url, proxy, credit_card):
        """
        Test the checkout process for a given URL, proxy, and credit card
        
        Args:
            url: The product URL to test
            proxy: Proxy string in format "ip:port:user:pass"
            credit_card: Dictionary with credit card details
            
        Returns:
            Dictionary with test results
        """
        print(f"\n{'='*80}")
        print(f"TESTING CHECKOUT: {url}")
        print(f"PROXY: {proxy}")
        print(f"CARD: {credit_card['number']}")
        print(f"{'='*80}\n")
        
        # Initialize ShopifyBot with the proxy
        bot = ShopifyBot(custom_proxy=proxy)
        
        # Step 1: Fetch product information
        product_info = bot.fetch_product_info(url)
        if not product_info:
            return {"status": "error", "message": "Failed to fetch product information"}
            
        # Step 2: Find a variant to purchase
        variant = bot.find_lowest_price_variant()
        if not variant:
            return {"status": "error", "message": "No available variants found"}
            
        # Step 3: Add to cart
        add_to_cart_result = bot.add_to_cart(variant['id'])
        if not add_to_cart_result:
            return {"status": "error", "message": "Failed to add product to cart"}
            
        # Step 4: Extract session cookies
        cookies_dict = {cookie.name: cookie.value for cookie in bot.session.cookies}
        print(f"Session cookies: {json.dumps(cookies_dict, indent=2)}")
        
        # Step 5: Get checkout URL
        checkout_url = bot.get_checkout_url()
        if not checkout_url:
            return {"status": "error", "message": "Failed to get checkout URL"}
            
        print(f"Checkout URL: {checkout_url}")
        
        # Step 6: Generate random user data for shipping/billing
        user_data = self.generate_random_user_data()
        
        # Step 7: Submit shipping information
        # The ShopifyBot class has hardcoded shipping information
        shipping_result = bot.submit_shipping_info()
        if not shipping_result:
            return {"status": "error", "message": "Failed to submit shipping information"}
            
        # Step 8: Submit payment information
        payment_result = bot.process_payment(
            credit_card["number"],
            credit_card["month"],
            credit_card["year"],
            credit_card["cvv"]
        )
        
        # Step 9: Check for success or error message
        if payment_result.get("success"):
            return {
                "status": "success",
                "message": "Payment successful",
                "details": payment_result
            }
        else:
            return {
                "status": "error",
                "message": payment_result.get("error", "Payment failed"),
                "details": payment_result
            }
    
    def run_tests(self):
        """Run tests with different combinations of URLs, proxies, and credit cards"""
        results = []
        
        for url in self.test_urls:
            # Use a random proxy and credit card for each test
            proxy = random.choice(self.proxies)
            card = random.choice(self.credit_cards)
            
            try:
                result = self.test_checkout(url, proxy, card)
                result["url"] = url
                result["proxy"] = proxy
                result["card"] = card["number"]
                results.append(result)
                
                # Print the result
                print(f"\nRESULT: {result['status']}")
                print(f"MESSAGE: {result['message']}")
                
                # Wait between tests to avoid rate limiting
                time.sleep(5)
                
            except Exception as e:
                print(f"Error during test: {str(e)}")
                results.append({
                    "status": "error",
                    "message": f"Exception: {str(e)}",
                    "url": url,
                    "proxy": proxy,
                    "card": card["number"]
                })
        
        return results

def main():
    tester = ShopifyCheckoutTester()
    results = tester.run_tests()
    
    # Save results to a file
    with open("checkout_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    print(f"Total tests: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    
    if success_count > 0:
        print("\nSuccessful tests:")
        for r in results:
            if r["status"] == "success":
                print(f"- {r['url']} with card {r['card']}")
    
    print("\nTest results saved to checkout_test_results.json")

if __name__ == "__main__":
    main()