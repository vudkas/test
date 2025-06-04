#!/usr/bin/env python3
"""
Manual Card Testing Helper for Shopify Sites
This script helps with manual testing of credit cards by providing formatted test data.
"""

import json
import os
import time
from datetime import datetime

# Test cards
TEST_CARDS = [
    {"number": "4213630013499628", "expiry_month": "09", "expiry_year": "2028", "cvv": "988"},
    {"number": "5356810054178190", "expiry_month": "06", "expiry_year": "2027", "cvv": "572"},
    {"number": "4622391115565643", "expiry_month": "11", "expiry_year": "2027", "cvv": "108"},
    {"number": "5509890032421892", "expiry_month": "11", "expiry_year": "2027", "cvv": "017"},
    {"number": "5455122807222246", "expiry_month": "06", "expiry_year": "2028", "cvv": "999"},
    {"number": "4632252055500305", "expiry_month": "12", "expiry_year": "2028", "cvv": "730"},
    {"number": "5169201653090928", "expiry_month": "03", "expiry_year": "2029", "cvv": "562"},
    {"number": "4411037149484856", "expiry_month": "05", "expiry_year": "2029", "cvv": "259"},
    {"number": "379186167572585", "expiry_month": "06", "expiry_year": "2025", "cvv": "2778"}
]

# Test sites
TEST_SITES = [
    {
        "name": "Era of Peace",
        "url": "https://eraofpeace.org/products/donation-1?utm_source=shop_app&list_generator=link_to_storefront&context=product&user_id=251069197"
    },
    {
        "name": "Zion Park",
        "url": "https://store.zionpark.org/products/donation?utm_source=shop_app&list_generator=link_to_storefront&context=product&user_id=251069197"
    }
]

# Customer information
CUSTOMER_INFO = {
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "address": "123 Test St",
    "city": "Test City",
    "state": "California",
    "zip": "90210",
    "phone": "5551234567"
}

def record_result(site_name, card, status, message, url):
    """Record a test result to a file."""
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "site": site_name,
        "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
        "status": status,
        "message": message,
        "url": url
    }
    
    # Load existing results if file exists
    results = []
    if os.path.exists("manual_test_results.json"):
        with open("manual_test_results.json", "r") as f:
            try:
                results = json.load(f)
            except:
                results = []
    
    # Add new result
    results.append(result)
    
    # Save results
    with open("manual_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Result recorded: {status} - {message}")

def main():
    """Main function to display test information."""
    print("\n=== Manual Card Testing Helper ===\n")
    
    print("Customer Information:")
    for key, value in CUSTOMER_INFO.items():
        print(f"  {key}: {value}")
    
    print("\nTest Sites:")
    for i, site in enumerate(TEST_SITES):
        print(f"  {i+1}. {site['name']}: {site['url']}")
    
    print("\nTest Cards:")
    for i, card in enumerate(TEST_CARDS):
        print(f"\n  Card {i+1}:")
        print(f"    Number: {card['number']}")
        print(f"    Expiry: {card['expiry_month']}/{card['expiry_year']}")
        print(f"    CVV: {card['cvv']}")
        print(f"    Formatted: {card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}")
    
    print("\nInstructions:")
    print("1. Visit one of the test sites")
    print("2. Add the product to cart and proceed to checkout")
    print("3. Fill in the customer information")
    print("4. Test each card and record the results")
    print("5. Use the record_result() function to save your findings")
    
    print("\nExample:")
    print("record_result('Era of Peace', TEST_CARDS[0], 'DECLINED', 'Your card was declined', 'https://example.com/checkout')")
    
    print("\nWaiting for your input...")
    
    # Make the record_result function available in the global scope
    globals()['record_result'] = record_result
    globals()['TEST_CARDS'] = TEST_CARDS
    globals()['TEST_SITES'] = TEST_SITES

if __name__ == "__main__":
    main()