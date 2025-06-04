"""
Shopify Automated Checkout Bot

This module provides a fully automated Shopify checkout bot that handles the entire process
from product selection to payment processing.
"""

import requests
import random
import string
import json
import time
import urllib.parse
import re
import os
import sys
import logging
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('shopify_bot')

class ShopifyBot:
    """
    A fully automated Shopify checkout bot that handles the entire process
    from product selection to payment processing.
    """
    
    def __init__(self, custom_proxy=None):
        """
        Initialize the Shopify Bot with session and proxy configuration.
        
        Args:
            custom_proxy: Optional proxy string in format "ip:port" or "ip:port:user:pass"
        """
        self.session = requests.Session()
        self.retry_count = 0
        self.max_retries = 3
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Set default headers for all requests
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Store checkout information
        self.product_info = {}
        self.checkout_url = None
        self.checkout_token = None
        self.shipping_url = None
        self.payment_url = None
        
        # Configure proxy if provided
        self.custom_proxy = custom_proxy
        self.configure_proxy()
        
    def configure_proxy(self):
        """
        Configure the proxy for the session.
        
        Args:
            custom_proxy: Proxy string in format "ip:port" or "ip:port:user:pass"
        """
        if not self.custom_proxy:
            logger.info("No proxy configured")
            return
            
        try:
            parts = self.custom_proxy.split(':')
            if len(parts) == 2:  # IP:PORT format
                proxy_url = f"http://{parts[0]}:{parts[1]}"
            elif len(parts) == 4:  # IP:PORT:USER:PASS format
                proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            else:
                logger.warning("Invalid proxy format")
                return
                
            self.session.proxies.update({
                'http': proxy_url,
                'https': proxy_url
            })
            logger.info(f"{Fore.GREEN}Proxy configured successfully{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}Error configuring proxy: {e}{Style.RESET_ALL}")
            
    def generate_random_string(self, length):
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def extract_between(self, text, start, end):
        """Extract text between two markers"""
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return None
            start_idx += len(start)
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return None
            return text[start_idx:end_idx]
        except Exception:
            return None
            
    def fetch_product_info(self, product_url):
        """
        Fetch product information from a Shopify product URL.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with product information including variants
        """
        logger.info(f"{Fore.BLUE}Fetching product information from: {product_url}{Style.RESET_ALL}")
        
        try:
            response = self.session.get(product_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"{Fore.RED}Failed to get product page: {response.status_code}{Style.RESET_ALL}")
                return None
                
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract product title
            product_title = None
            title_elem = soup.select_one('h1.product-single__title, h1.product__title, h1')
            if title_elem:
                product_title = title_elem.text.strip()
            
            # Extract product price
            product_price = None
            price_elem = soup.select_one('[data-product-price], .price__current, .product__price')
            if price_elem:
                price_text = price_elem.text.strip()
                # Extract digits and decimal point from price text
                price_match = re.search(r'[\d,.]+', price_text)
                if price_match:
                    product_price = price_match.group(0).replace(',', '')
            
            # Extract product variants
            variants = []
            
            # Method 1: Look for variants in JSON data
            json_match = re.search(r'var\s+meta\s*=\s*({.*?});', response.text, re.DOTALL) or \
                         re.search(r'window\.meta\s*=\s*({.*?});', response.text, re.DOTALL) or \
                         re.search(r'var\s+product\s*=\s*({.*?});', response.text, re.DOTALL)
                         
            if json_match:
                try:
                    product_json = json.loads(json_match.group(1))
                    if 'product' in product_json:
                        product_data = product_json['product']
                        if 'variants' in product_data:
                            for variant in product_data['variants']:
                                variant_info = {
                                    'id': variant.get('id'),
                                    'title': variant.get('title'),
                                    'price': variant.get('price'),
                                    'available': variant.get('available', True)
                                }
                                variants.append(variant_info)
                except json.JSONDecodeError:
                    pass
            
            # Method 2: Look for variant options in select elements
            if not variants:
                variant_selects = soup.select('select[name="id"], select[id*="ProductSelect"]')
                for select in variant_selects:
                    for option in select.select('option'):
                        if option.get('value') and not option.get('disabled'):
                            price_text = option.text
                            price_match = re.search(r'[\d,.]+', price_text)
                            price = price_match.group(0).replace(',', '') if price_match else None
                            
                            variant_info = {
                                'id': option.get('value'),
                                'title': option.text.strip(),
                                'price': price,
                                'available': True
                            }
                            variants.append(variant_info)
            
            # If no variants found, create a default variant with the product price
            if not variants:
                # Try to find variant ID in the page
                variant_id_match = re.search(r'"id":(\d+),"available":true', response.text) or \
                                  re.search(r'value="(\d+)"[^>]*>.*?</option>', response.text) or \
                                  re.search(r'name="id"[^>]*value="(\d+)"', response.text)
                                  
                if variant_id_match:
                    variant_id = variant_id_match.group(1)
                    variants.append({
                        'id': variant_id,
                        'title': 'Default',
                        'price': product_price,
                        'available': True
                    })
            
            # Store product information
            self.product_info = {
                'title': product_title,
                'price': product_price,
                'url': product_url,
                'variants': variants,
                'domain': urlparse(product_url).netloc
            }
            
            # Print product information
            logger.info(f"{Fore.GREEN}Product: {product_title}{Style.RESET_ALL}")
            logger.info(f"{Fore.GREEN}Price: {product_price}{Style.RESET_ALL}")
            logger.info(f"{Fore.GREEN}Found {len(variants)} variants{Style.RESET_ALL}")
            
            return self.product_info
            
        except Exception as e:
            logger.error(f"{Fore.RED}Error fetching product info: {e}{Style.RESET_ALL}")
            return None
    
    def find_lowest_price_variant(self):
        """
        Find the variant with the lowest price from the fetched product information.
        
        Returns:
            Dictionary with the lowest-priced variant information
        """
        if not self.product_info or 'variants' not in self.product_info or not self.product_info['variants']:
            logger.error(f"{Fore.RED}No product variants available{Style.RESET_ALL}")
            return None
            
        available_variants = [v for v in self.product_info['variants'] if v.get('available')]
        
        if not available_variants:
            logger.error(f"{Fore.RED}No available variants found{Style.RESET_ALL}")
            return None
            
        # Convert prices to float for comparison
        for variant in available_variants:
            if variant.get('price'):
                try:
                    variant['price_float'] = float(variant['price'])
                except (ValueError, TypeError):
                    variant['price_float'] = float('inf')
            else:
                variant['price_float'] = float('inf')
        
        # Find the lowest-priced variant
        lowest_price_variant = min(available_variants, key=lambda x: x.get('price_float', float('inf')))
        
        logger.info(f"{Fore.GREEN}Selected variant: {lowest_price_variant.get('title')}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Price: {lowest_price_variant.get('price')}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Variant ID: {lowest_price_variant.get('id')}{Style.RESET_ALL}")
        
        return lowest_price_variant
        
    def add_to_cart(self, variant_id):
        """
        Add a product variant to the cart.
        
        Args:
            variant_id: The ID of the variant to add to cart
            
        Returns:
            True if successful, False otherwise
        """
        if not self.product_info or 'domain' not in self.product_info:
            logger.error(f"{Fore.RED}No product information available{Style.RESET_ALL}")
            return False
            
        domain = self.product_info['domain']
        logger.info(f"{Fore.BLUE}Adding variant {variant_id} to cart on {domain}{Style.RESET_ALL}")
        
        # Try multiple cart endpoints to ensure compatibility
        cart_endpoints = [
            f"https://{domain}/cart/add.js",
            f"https://{domain}/cart/add",
            f"https://{domain}/cart/add.json"
        ]

        data = {
            'id': variant_id,
            'quantity': 1,
            'form_type': 'product',
            'utf8': '✓'
        }
        
        # Try each endpoint until one works
        for endpoint in cart_endpoints:
            try:
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': f'https://{domain}',
                    'Referer': self.product_info['url']
                }
                
                response = self.session.post(
                    endpoint, 
                    data=data, 
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in (200, 302):
                    logger.info(f"{Fore.GREEN}Successfully added to cart using {endpoint}{Style.RESET_ALL}")
                    
                    # Visit the cart page to set cookies and session
                    cart_url = f"https://{domain}/cart"
                    cart_response = self.session.get(cart_url, timeout=10)
                    
                    if cart_response.status_code == 200:
                        logger.info(f"{Fore.GREEN}Successfully accessed cart page{Style.RESET_ALL}")
                        return True
                    else:
                        logger.warning(f"{Fore.YELLOW}Failed to access cart page: {cart_response.status_code}{Style.RESET_ALL}")
                        # Continue anyway since we already added to cart
                        return True
            except Exception as e:
                logger.warning(f"{Fore.YELLOW}Failed with endpoint {endpoint}: {e}{Style.RESET_ALL}")
                continue
                
        logger.error(f"{Fore.RED}All cart endpoints failed{Style.RESET_ALL}")
        return False
        
    def get_checkout_url(self):
        """
        Get the checkout URL after adding items to cart.
        
        Returns:
            The checkout URL if successful, None otherwise
        """
        if not self.product_info or 'domain' not in self.product_info:
            logger.error(f"{Fore.RED}No product information available{Style.RESET_ALL}")
            return None
            
        domain = self.product_info['domain']
        logger.info(f"{Fore.BLUE}Getting checkout URL for domain: {domain}{Style.RESET_ALL}")
        
        try:
            # First try the standard checkout endpoint
            response = self.session.get(
                f"https://{domain}/checkout", 
                allow_redirects=True,
                timeout=10
            )
            
            logger.info(f"Checkout response status: {response.status_code}, URL: {response.url}")
            
            # Check if we were redirected to a checkout URL
            if 'checkout' in response.url:
                parsed_url = urlparse(response.url)
                self.checkout_url = response.url
                
                # Extract checkout token if available
                if 'checkouts' in parsed_url.path:
                    self.checkout_token = parsed_url.path.split('/')[-1]
                    logger.info(f"{Fore.GREEN}Found checkout token: {self.checkout_token}{Style.RESET_ALL}")
                
                logger.info(f"{Fore.GREEN}Checkout URL: {self.checkout_url}{Style.RESET_ALL}")
                
                # Extract session cookies
                cookies_dict = {cookie.name: cookie.value for cookie in self.session.cookies}
                logger.info(f"{Fore.GREEN}Session cookies: {json.dumps(cookies_dict, indent=2)}{Style.RESET_ALL}")
                
                return self.checkout_url
            else:
                # Try alternative method - get checkout from cart page
                cart_response = self.session.get(
                    f"https://{domain}/cart", 
                    allow_redirects=True,
                    timeout=10
                )
                
                # Look for checkout URL in the cart page
                checkout_match = re.search(r'action="([^"]*checkout[^"]*)"', cart_response.text)
                if checkout_match:
                    checkout_path = checkout_match.group(1)
                    if checkout_path.startswith('/'):
                        self.checkout_url = f"https://{domain}{checkout_path}"
                    else:
                        self.checkout_url = checkout_path
                        
                    logger.info(f"{Fore.GREEN}Found checkout URL from cart: {self.checkout_url}{Style.RESET_ALL}")
                    return self.checkout_url
                    
            logger.error(f"{Fore.RED}Could not find checkout URL{Style.RESET_ALL}")
            return None
        except Exception as e:
            logger.error(f"{Fore.RED}Error getting checkout URL: {e}{Style.RESET_ALL}")
            return None
            
    def extract_form_data(self, html_content):
        """
        Extract hidden form fields and authenticity token from HTML content.
        
        Args:
            html_content: HTML content of the page
            
        Returns:
            Dictionary of form field names and values
        """
        form_data = {}
        
        # Extract authenticity token
        auth_token_match = re.search(r'name="authenticity_token"[^>]*value="([^"]*)"', html_content)
        if auth_token_match:
            form_data['authenticity_token'] = auth_token_match.group(1)
            
        # Extract other hidden fields
        hidden_fields = re.findall(r'<input type="hidden" name="([^"]*)" value="([^"]*)"', html_content)
        for name, value in hidden_fields:
            form_data[name] = value
            
        return form_data
        
    def submit_shipping_info(self):
        """
        Submit shipping information to the checkout page.
        
        Returns:
            The URL of the next step if successful, None otherwise
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
            
            # Add shipping information to form data
            shipping_data = {
                'checkout[email]': 'raven.usu@gmail.com',
                'checkout[shipping_address][first_name]': 'John',
                'checkout[shipping_address][last_name]': 'Doe',
                'checkout[shipping_address][address1]': '123 Main St',
                'checkout[shipping_address][address2]': '',
                'checkout[shipping_address][city]': 'New York',
                'checkout[shipping_address][country]': 'United States',
                'checkout[shipping_address][province]': 'New York',
                'checkout[shipping_address][zip]': '10001',
                'checkout[shipping_address][phone]': '2125551234',
                'checkout[remember_me]': '0',
                'checkout[client_details][browser_width]': '1920',
                'checkout[client_details][browser_height]': '1080',
                'checkout[client_details][javascript_enabled]': '1',
                'step': 'contact_information'
            }
            
            # Merge form data with shipping data
            form_data.update(shipping_data)
            
            # Submit shipping information
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self.checkout_url.split('/checkouts')[0],
                'Referer': self.checkout_url
            }
            
            # Determine the submission URL
            if '/checkouts/' in self.checkout_url:
                submit_url = self.checkout_url
            else:
                submit_url = f"{self.checkout_url}/processing"
                
            shipping_response = self.session.post(
                submit_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=10
            )
            
            # Check if we were redirected to the shipping method page
            if shipping_response.status_code in (200, 302):
                self.shipping_url = shipping_response.url
                logger.info(f"{Fore.GREEN}Shipping info submitted successfully, next URL: {self.shipping_url}{Style.RESET_ALL}")
                return self.shipping_url
            else:
                logger.error(f"{Fore.RED}Failed to submit shipping info: {shipping_response.status_code}{Style.RESET_ALL}")
                return None
        except Exception as e:
            logger.error(f"{Fore.RED}Error submitting shipping info: {e}{Style.RESET_ALL}")
            return None
            
    def select_shipping_method(self):
        """
        Select a shipping method on the shipping page.
        
        Returns:
            The URL of the next step if successful, None otherwise
        """
        if not self.shipping_url:
            logger.error(f"{Fore.RED}No shipping URL available{Style.RESET_ALL}")
            return None
            
        try:
            logger.info(f"{Fore.BLUE}Selecting shipping method at: {self.shipping_url}{Style.RESET_ALL}")
            
            # Get the shipping page to extract available methods
            shipping_response = self.session.get(self.shipping_url, timeout=10)
            if shipping_response.status_code != 200:
                logger.error(f"{Fore.RED}Failed to get shipping page: {shipping_response.status_code}{Style.RESET_ALL}")
                return None
                
            # Extract form data from the page
            form_data = self.extract_form_data(shipping_response.text)
            
            # Look for available shipping methods
            shipping_methods = re.findall(r'<input[^>]*name="checkout\[shipping_rate\]\[id\]"[^>]*value="([^"]*)"', shipping_response.text)
            
            if shipping_methods:
                # Select the first available shipping method
                form_data['checkout[shipping_rate][id]'] = shipping_methods[0]
                logger.info(f"{Fore.GREEN}Selected shipping method: {shipping_methods[0]}{Style.RESET_ALL}")
            else:
                logger.warning(f"{Fore.YELLOW}No shipping methods found, continuing anyway{Style.RESET_ALL}")
                
            # Add step information
            form_data['step'] = 'shipping_method'
            
            # Submit shipping method selection
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self.shipping_url.split('/checkouts')[0],
                'Referer': self.shipping_url
            }
            
            shipping_method_response = self.session.post(
                self.shipping_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=10
            )
            
            # Check if we were redirected to the payment page
            if shipping_method_response.status_code in (200, 302):
                self.payment_url = shipping_method_response.url
                logger.info(f"{Fore.GREEN}Shipping method selected successfully, next URL: {self.payment_url}{Style.RESET_ALL}")
                return self.payment_url
            else:
                logger.error(f"{Fore.RED}Failed to select shipping method: {shipping_method_response.status_code}{Style.RESET_ALL}")
                return None
        except Exception as e:
            logger.error(f"{Fore.RED}Error selecting shipping method: {e}{Style.RESET_ALL}")
            return None
            
    def process_payment(self, cc, month, year, cvv):
        """
        Process payment on the payment page.
        
        Args:
            cc: Credit card number
            month: Expiration month (2 digits)
            year: Expiration year (2 or 4 digits)
            cvv: Card verification value
            
        Returns:
            Dictionary with payment result information
        """
        if not self.payment_url:
            logger.error(f"{Fore.RED}No payment URL available{Style.RESET_ALL}")
            return {"status": False, "message": "No payment URL available"}
            
        try:
            logger.info(f"{Fore.BLUE}Processing payment at: {self.payment_url}{Style.RESET_ALL}")
            
            # Get the payment page to extract payment gateway information
            payment_response = self.session.get(self.payment_url, timeout=10)
            if payment_response.status_code != 200:
                logger.error(f"{Fore.RED}Failed to get payment page: {payment_response.status_code}{Style.RESET_ALL}")
                return {"status": False, "message": "Failed to access payment page"}
                
            # Extract form data and payment gateway information
            form_data = self.extract_form_data(payment_response.text)
            
            # Extract payment gateway ID
            gateway_id_match = re.search(r'data-gateway-id="([^"]*)"', payment_response.text) or \
                              re.search(r'name="checkout\[payment_gateway\]"[^>]*value="([^"]*)"', payment_response.text)
                              
            if gateway_id_match:
                gateway_id = gateway_id_match.group(1)
                form_data['checkout[payment_gateway]'] = gateway_id
                logger.info(f"{Fore.GREEN}Found payment gateway ID: {gateway_id}{Style.RESET_ALL}")
            else:
                logger.warning(f"{Fore.YELLOW}Could not find payment gateway ID{Style.RESET_ALL}")
            
            # Extract payment session ID if available
            session_id_match = re.search(r'data-payment-session-id="([^"]*)"', payment_response.text)
            if session_id_match:
                session_id = session_id_match.group(1)
                form_data['checkout[payment_session_id]'] = session_id
                logger.info(f"{Fore.GREEN}Found payment session ID: {session_id}{Style.RESET_ALL}")
            
            # Format card data
            if len(year) == 2:
                formatted_year = f"20{year}"
            else:
                formatted_year = year
                
            # Add payment information to form data
            payment_data = {
                'checkout[credit_card][number]': cc,
                'checkout[credit_card][name]': "John Doe",
                'checkout[credit_card][month]': month,
                'checkout[credit_card][year]': formatted_year,
                'checkout[credit_card][verification_value]': cvv,
                'checkout[different_billing_address]': 'false',
                'checkout[remember_me]': 'false',
                'checkout[vault_phone]': 'false',
                'complete': '1',
                'step': 'payment_method'
            }
            
            # Merge form data with payment data
            form_data.update(payment_data)
            
            # Submit payment
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self.payment_url.split('/checkouts')[0],
                'Referer': self.payment_url
            }
            
            logger.info(f"{Fore.BLUE}Submitting payment...{Style.RESET_ALL}")
            
            payment_response = self.session.post(
                self.payment_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=15  # Longer timeout for payment processing
            )
            
            # Parse the payment result
            return self.parse_payment_result(payment_response)
            
        except Exception as e:
            logger.error(f"{Fore.RED}Error processing payment: {e}{Style.RESET_ALL}")
            return {"status": False, "message": f"Payment processing error: {str(e)}"}
            
    def parse_payment_result(self, response):
        """
        Parse the payment response to determine the result.
        
        Args:
            response: The payment response
            
        Returns:
            Dictionary with payment result information
        """
        try:
            # Check if we were redirected to a thank you page
            if 'thank_you' in response.url or 'order-status' in response.url or 'orders' in response.url:
                logger.info(f"{Fore.GREEN}✅ Payment successful - redirected to thank you page{Style.RESET_ALL}")
                
                # Try to extract order number
                order_match = re.search(r'order[_-]([a-zA-Z0-9]+)', response.url)
                order_id = order_match.group(1) if order_match else "unknown"
                
                return {
                    "status": True,
                    "result": "✅ Approved - Charged",
                    "message": "Payment successful",
                    "order_id": order_id,
                    "redirect_url": response.url
                }
                
            # Check for 3D Secure redirect
            elif '3d_secure' in response.url or 'cardinal' in response.url or 'authenticate' in response.url:
                logger.info(f"{Fore.YELLOW}⚠️ 3D Secure authentication required{Style.RESET_ALL}")
                return {
                    "status": False,
                    "result": "⚠️ 3D Secure Required",
                    "message": "3D Secure authentication required",
                    "redirect_url": response.url
                }
                
            # Check for payment errors in the response content
            content = response.text.lower()
            
            if 'card was declined' in content or 'declined' in content:
                logger.warning(f"{Fore.RED}❌ Payment declined{Style.RESET_ALL}")
                return {
                    "status": False,
                    "result": "❌ Declined",
                    "message": "Card was declined"
                }
                
            elif 'invalid' in content and ('card' in content or 'number' in content):
                logger.warning(f"{Fore.RED}❌ Invalid card number{Style.RESET_ALL}")
                return {
                    "status": False,
                    "result": "❌ Invalid Card",
                    "message": "Invalid card number"
                }
                
            elif 'expired' in content:
                logger.warning(f"{Fore.RED}❌ Expired card{Style.RESET_ALL}")
                return {
                    "status": False,
                    "result": "❌ Expired Card",
                    "message": "Card has expired"
                }
                
            elif 'cvv' in content or 'security code' in content or 'verification value' in content:
                logger.warning(f"{Fore.RED}❌ Invalid CVV{Style.RESET_ALL}")
                return {
                    "status": False,
                    "result": "❌ Invalid CVV",
                    "message": "Invalid security code"
                }
                
            # Default to unknown error
            logger.error(f"{Fore.RED}❌ Unknown payment result{Style.RESET_ALL}")
            return {
                "status": False,
                "result": "❌ Unknown",
                "message": "Payment processing failed with unknown error"
            }
        except Exception as e:
            logger.error(f"{Fore.RED}Error parsing payment result: {e}{Style.RESET_ALL}")
            return {
                "status": False,
                "result": "❌ Error",
                "message": f"Error parsing payment result: {str(e)}"
            }
            
    def run_checkout(self, product_url, cc=None, month=None, year=None, cvv=None):
        """
        Run the complete checkout process for a Shopify product.
        
        Args:
            product_url: URL of the product to purchase
            cc: Credit card number (optional)
            month: Expiration month (optional)
            year: Expiration year (optional)
            cvv: Card verification value (optional)
            
        Returns:
            Dictionary with checkout result information
        """
        logger.info(f"{Fore.BLUE}Starting checkout process for: {product_url}{Style.RESET_ALL}")
        
        # Step 1: Fetch product information
        product_info = self.fetch_product_info(product_url)
        if not product_info:
            return {"status": False, "message": "Failed to fetch product information"}
            
        # Step 2: Find the lowest-priced variant
        variant = self.find_lowest_price_variant()
        if not variant:
            return {"status": False, "message": "Failed to find available variant"}
            
        # Step 3: Add to cart
        add_result = self.add_to_cart(variant['id'])
        if not add_result:
            return {"status": False, "message": "Failed to add product to cart"}
            
        # Step 4: Get checkout URL
        checkout_url = self.get_checkout_url()
        if not checkout_url:
            return {"status": False, "message": "Failed to get checkout URL"}
            
        # If no payment details provided, stop here and return checkout URL
        if not all([cc, month, year, cvv]):
            cookies_dict = {cookie.name: cookie.value for cookie in self.session.cookies}
            return {
                "status": True,
                "message": "Added to cart successfully",
                "product": product_info['title'],
                "variant": variant['title'],
                "price": variant['price'],
                "cookies": cookies_dict,
                "checkout_url": checkout_url
            }
            
        # Step 5: Submit shipping information
        shipping_url = self.submit_shipping_info()
        if not shipping_url:
            return {"status": False, "message": "Failed to submit shipping information"}
            
        # Step 6: Select shipping method
        payment_url = self.select_shipping_method()
        if not payment_url:
            return {"status": False, "message": "Failed to select shipping method"}
            
        # Step 7: Process payment
        payment_result = self.process_payment(cc, month, year, cvv)
        
        # Add product information to the result
        payment_result.update({
            "product": product_info['title'],
            "variant": variant['title'],
            "price": variant['price']
        })
        
        return payment_result


def main():
    """
    Main function to run the Shopify checkout bot from command line.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Shopify Checkout Bot')
    parser.add_argument('--url', required=True, help='Product URL')
    parser.add_argument('--proxy', help='Proxy in format ip:port or ip:port:user:pass')
    
    # Optional payment details
    parser.add_argument('--cc', help='Credit card number')
    parser.add_argument('--month', help='Expiration month (2 digits)')
    parser.add_argument('--year', help='Expiration year (2 or 4 digits)')
    parser.add_argument('--cvv', help='Card verification value')
    
    args = parser.parse_args()
    
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
    print("\nCheckout Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()