#!/usr/bin/env python3
"""
Enhanced Shopify Checkout Tester

This script extends the ShopifyBot class to add better testing capabilities
and runs tests with the provided proxies and credit cards.
"""

import sys
import json
import time
import re
import random
import logging
import argparse
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Import the ShopifyBot class
from shopify_bot import ShopifyBot

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('enhanced_tester')

class EnhancedShopifyBot(ShopifyBot):
    """
    Enhanced version of ShopifyBot with additional testing capabilities
    """
    
    def __init__(self, custom_proxy=None, user_data=None):
        """
        Initialize the Enhanced ShopifyBot
        
        Args:
            custom_proxy: Optional proxy string in format "ip:port" or "ip:port:user:pass"
            user_data: Optional dictionary with user data for shipping/billing
        """
        super().__init__(custom_proxy)
        self.user_data = user_data or self.generate_random_user_data()
        self.test_results = {
            "product_info": None,
            "add_to_cart": None,
            "checkout_url": None,
            "shipping_info": None,
            "payment_info": None,
            "final_result": None
        }
        
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
        
    def submit_shipping_info(self):
        """
        Override the submit_shipping_info method to use our custom user data
        """
        if not self.checkout_url:
            logger.error(f"{Fore.RED}No checkout URL available{Style.RESET_ALL}")
            return None

        try:
            logger.info(f"{Fore.BLUE}Submitting shipping info to: {self.checkout_url}{Style.RESET_ALL}")

            # Get the checkout page to extract form data
            checkout_response = self.session.get(self.checkout_url, timeout=10)
            if checkout_response.status_code != 200:
                logger.error(f"{Fore.RED}Failed to get checkout page: {checkout_response.status_code}{Style.RESET_ALL}")
                return None

            # Extract form data from the page
            form_data = self.extract_form_data(checkout_response.text)

            # Add shipping information to form data using our custom user data
            shipping_data = {
                'checkout[email]': self.user_data.get('email', 'raven.usu@gmail.com'),
                'checkout[shipping_address][first_name]': self.user_data.get('first_name', 'John'),
                'checkout[shipping_address][last_name]': self.user_data.get('last_name', 'Doe'),
                'checkout[shipping_address][address1]': self.user_data.get('address1', '123 Main St'),
                'checkout[shipping_address][address2]': self.user_data.get('address2', ''),
                'checkout[shipping_address][city]': self.user_data.get('city', 'New York'),
                'checkout[shipping_address][country]': self.user_data.get('country', 'United States'),
                'checkout[shipping_address][province]': self.user_data.get('state', 'NY'),
                'checkout[shipping_address][zip]': self.user_data.get('zip', '10001'),
                'checkout[shipping_address][phone]': self.user_data.get('phone', '2125551234'),
                'checkout[remember_me]': '0',
                'checkout[client_details][browser_width]': '1920',
                'checkout[client_details][browser_height]': '1080',
                'checkout[client_details][javascript_enabled]': '1',
                'checkout[client_details][color_depth]': '24',
                'checkout[client_details][java_enabled]': 'false',
                'checkout[client_details][browser_tz]': '-240'
            }

            # Update form data with shipping information
            form_data.update(shipping_data)

            # Submit the form
            shipping_url = self.checkout_url
            if not shipping_url.endswith('/shipping_method'):
                shipping_url = f"{self.checkout_url}/shipping_method"
                
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': f"https://{self.product_info['domain']}",
                'Referer': self.checkout_url
            }
            
            shipping_response = self.session.post(
                shipping_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=10
            )
            
            # Check if we were redirected to the shipping method page
            if shipping_response.status_code in (200, 302):
                # Extract the next URL from the response
                next_url = shipping_response.url
                self.shipping_url = next_url
                
                logger.info(f"{Fore.GREEN}Successfully submitted shipping info{Style.RESET_ALL}")
                logger.info(f"{Fore.GREEN}Next URL: {next_url}{Style.RESET_ALL}")
                
                # Store the result
                self.test_results["shipping_info"] = {
                    "success": True,
                    "url": next_url
                }
                
                return next_url
            else:
                logger.error(f"{Fore.RED}Failed to submit shipping info: {shipping_response.status_code}{Style.RESET_ALL}")
                
                # Store the result
                self.test_results["shipping_info"] = {
                    "success": False,
                    "status_code": shipping_response.status_code
                }
                
                return None
                
        except Exception as e:
            logger.error(f"{Fore.RED}Error submitting shipping info: {e}{Style.RESET_ALL}")
            
            # Store the result
            self.test_results["shipping_info"] = {
                "success": False,
                "error": str(e)
            }
            
            return None
            
    def run_full_test(self, product_url, cc, month, year, cvv):
        """
        Run a full checkout test with the given product URL and payment details
        
        Args:
            product_url: URL of the product to test
            cc: Credit card number
            month: Expiration month
            year: Expiration year
            cvv: CVV code
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"{Fore.BLUE}Starting full checkout test for: {product_url}{Style.RESET_ALL}")
        logger.info(f"{Fore.BLUE}Using proxy: {self.custom_proxy}{Style.RESET_ALL}")
        
        # Step 1: Fetch product information
        product_info = self.fetch_product_info(product_url)
        if not product_info:
            self.test_results["final_result"] = {
                "success": False,
                "message": "Failed to fetch product information"
            }
            return self.test_results
            
        self.test_results["product_info"] = {
            "success": True,
            "title": product_info.get("title"),
            "price": product_info.get("price"),
            "variants_count": len(product_info.get("variants", []))
        }
        
        # Step 2: Find a variant to purchase
        variant = self.find_lowest_price_variant()
        if not variant:
            self.test_results["final_result"] = {
                "success": False,
                "message": "No available variants found"
            }
            return self.test_results
            
        # Step 3: Add to cart
        add_to_cart_result = self.add_to_cart(variant['id'])
        self.test_results["add_to_cart"] = {
            "success": add_to_cart_result,
            "variant_id": variant['id']
        }
        
        if not add_to_cart_result:
            self.test_results["final_result"] = {
                "success": False,
                "message": "Failed to add product to cart"
            }
            return self.test_results
            
        # Step 4: Extract session cookies
        cookies_dict = {cookie.name: cookie.value for cookie in self.session.cookies}
        logger.info(f"{Fore.GREEN}Session cookies extracted{Style.RESET_ALL}")
        
        # Step 5: Get checkout URL
        checkout_url = self.get_checkout_url()
        self.test_results["checkout_url"] = {
            "success": bool(checkout_url),
            "url": checkout_url
        }
        
        if not checkout_url:
            self.test_results["final_result"] = {
                "success": False,
                "message": "Failed to get checkout URL"
            }
            return self.test_results
            
        # Step 6: Submit shipping information
        shipping_result = self.submit_shipping_info()
        if not shipping_result:
            self.test_results["final_result"] = {
                "success": False,
                "message": "Failed to submit shipping information"
            }
            return self.test_results
            
        # Step 7: Process payment
        payment_result = self.process_payment(cc, month, year, cvv)
        self.test_results["payment_info"] = payment_result
        
        # Step 8: Set final result
        if payment_result.get("success"):
            self.test_results["final_result"] = {
                "success": True,
                "message": "Payment successful",
                "thank_you_page": payment_result.get("thank_you_page", False)
            }
        else:
            self.test_results["final_result"] = {
                "success": False,
                "message": payment_result.get("error", "Payment failed")
            }
            
        return self.test_results


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
        
    def run_tests(self, specific_url=None, specific_proxy=None, specific_card=None):
        """
        Run tests with different combinations of URLs, proxies, and credit cards
        
        Args:
            specific_url: Optional specific URL to test
            specific_proxy: Optional specific proxy to use
            specific_card: Optional specific card index to use
            
        Returns:
            List of test results
        """
        results = []
        
        # Use specific URL if provided, otherwise use all test URLs
        urls_to_test = [specific_url] if specific_url else self.test_urls
        
        # Use specific proxy if provided, otherwise use all proxies
        proxies_to_test = [specific_proxy] if specific_proxy else self.proxies
        
        # Use specific card if provided, otherwise use all cards
        cards_to_test = [self.credit_cards[specific_card]] if specific_card is not None else self.credit_cards
        
        for url in urls_to_test:
            # Use a random proxy and credit card for each test if not specified
            proxy = random.choice(proxies_to_test) if len(proxies_to_test) > 1 else proxies_to_test[0]
            card = random.choice(cards_to_test) if len(cards_to_test) > 1 else cards_to_test[0]
            
            logger.info(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}")
            logger.info(f"{Fore.BLUE}TESTING CHECKOUT: {url}{Style.RESET_ALL}")
            logger.info(f"{Fore.BLUE}PROXY: {proxy}{Style.RESET_ALL}")
            logger.info(f"{Fore.BLUE}CARD: {card['number']}{Style.RESET_ALL}")
            logger.info(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}")
            
            try:
                # Initialize the enhanced bot with the proxy
                bot = EnhancedShopifyBot(custom_proxy=proxy)
                
                # Run the full test
                result = bot.run_full_test(
                    url,
                    card["number"],
                    card["month"],
                    card["year"],
                    card["cvv"]
                )
                
                # Add test metadata
                result["url"] = url
                result["proxy"] = proxy
                result["card"] = card["number"]
                
                # Add to results
                results.append(result)
                
                # Print the result
                if result["final_result"]["success"]:
                    logger.info(f"{Fore.GREEN}TEST RESULT: SUCCESS{Style.RESET_ALL}")
                    logger.info(f"{Fore.GREEN}MESSAGE: {result['final_result']['message']}{Style.RESET_ALL}")
                else:
                    logger.info(f"{Fore.RED}TEST RESULT: FAILURE{Style.RESET_ALL}")
                    logger.info(f"{Fore.RED}MESSAGE: {result['final_result']['message']}{Style.RESET_ALL}")
                
                # Wait between tests to avoid rate limiting
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"{Fore.RED}Error during test: {str(e)}{Style.RESET_ALL}")
                results.append({
                    "final_result": {
                        "success": False,
                        "message": f"Exception: {str(e)}"
                    },
                    "url": url,
                    "proxy": proxy,
                    "card": card["number"]
                })
        
        return results


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Enhanced Shopify Checkout Tester')
    parser.add_argument('--url', help='Specific URL to test')
    parser.add_argument('--proxy', help='Specific proxy to use')
    parser.add_argument('--card', type=int, choices=[0, 1, 2, 3], help='Specific card index to use (0-3)')
    args = parser.parse_args()
    
    # Initialize the tester
    tester = ShopifyCheckoutTester()
    
    # Run the tests
    results = tester.run_tests(
        specific_url=args.url,
        specific_proxy=args.proxy,
        specific_card=args.card
    )
    
    # Save results to a file
    with open("enhanced_checkout_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    logger.info(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}")
    logger.info(f"{Fore.BLUE}TEST SUMMARY{Style.RESET_ALL}")
    logger.info(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}")
    
    success_count = sum(1 for r in results if r.get("final_result", {}).get("success", False))
    error_count = len(results) - success_count
    
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {error_count}")
    
    if success_count > 0:
        logger.info("\nSuccessful tests:")
        for r in results:
            if r.get("final_result", {}).get("success", False):
                logger.info(f"- {r['url']} with card {r['card']}")
    
    logger.info("\nTest results saved to enhanced_checkout_test_results.json")


if __name__ == "__main__":
    main()