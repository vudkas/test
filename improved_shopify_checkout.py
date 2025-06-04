"""
Shopify Checkout Automation - For Educational Purposes Only

This module provides a clean, modular implementation of Shopify checkout automation.
It is intended for educational purposes, authorized testing, or merchant-approved use only.

IMPORTANT: Automated checkout scripts may violate Shopify's Terms of Service.
Only use this code in compliance with all applicable terms, laws, and regulations.
"""

import requests
import random
import string
import json
import time
import re
import logging
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional, Tuple, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('shopify_checkout')

class ShopifyCheckout:
    """
    A class to handle Shopify checkout processes through API requests.
    
    This class provides methods to:
    1. Add products to cart
    2. Navigate to checkout
    3. Submit shipping information
    4. Process payment
    5. Handle various response types
    
    For educational and authorized testing purposes only.
    """
    
    def __init__(self, custom_proxy: Optional[str] = None):
        """
        Initialize the ShopifyCheckout with session and proxy configuration.
        
        Args:
            custom_proxy: Optional proxy string in format "ip:port" or "ip:port:user:pass"
        """
        self.session = requests.Session()
        self.retry_count = 0
        self.max_retries = 3
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Set default headers
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
        
        # Configure proxy if provided
        self.configure_proxy(custom_proxy)

    def configure_proxy(self, custom_proxy: Optional[str] = None) -> None:
        """
        Configure the proxy for the session.
        
        Args:
            custom_proxy: Proxy string in format "ip:port" or "ip:port:user:pass"
        """
        if not custom_proxy:
            logger.info("No proxy configured")
            return
            
        try:
            parts = custom_proxy.split(':')
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
            logger.info("Proxy configured successfully")
        except Exception as e:
            logger.error(f"Error configuring proxy: {e}")

    def get_product_variant_id(self, product_url: str) -> Optional[str]:
        """
        Extract the product variant ID from a product page.
        
        Args:
            product_url: Full URL to the product page
            
        Returns:
            The variant ID if found, None otherwise
        """
        try:
            logger.info(f"Getting product variant ID from: {product_url}")
            response = self.session.get(product_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to get product page: {response.status_code}")
                return None
                
            # Look for variant ID in the page content
            content = response.text
            
            # Method 1: Look for variant ID in JSON data
            variant_match = re.search(r'"id":(\d+),"available":true', content)
            if variant_match:
                return variant_match.group(1)
                
            # Method 2: Look for variant ID in select element
            select_match = re.search(r'<option[^>]*value="(\d+)"[^>]*>.*?</option>', content)
            if select_match:
                return select_match.group(1)
                
            # Method 3: Look for variant ID in form input
            input_match = re.search(r'<input[^>]*name="id"[^>]*value="(\d+)"', content)
            if input_match:
                return input_match.group(1)
                
            logger.warning("Could not find variant ID")
            return None
        except Exception as e:
            logger.error(f"Error getting product variant ID: {e}")
            return None

    def add_to_cart(self, domain: str, variant_id: str) -> bool:
        """
        Add a product to the cart.
        
        Args:
            domain: The shop domain (e.g., "example.myshopify.com")
            variant_id: The product variant ID to add to cart
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Adding variant {variant_id} to cart on {domain}")
            
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
                        'Referer': f'https://{domain}/products/any'
                    }
                    
                    response = self.session.post(
                        endpoint, 
                        data=data, 
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code in (200, 302):
                        logger.info(f"Successfully added to cart using {endpoint}")
                        return True
                except Exception as e:
                    logger.warning(f"Failed with endpoint {endpoint}: {e}")
                    continue
                    
            logger.error("All cart endpoints failed")
            return False
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False

    def get_checkout_url(self, domain: str) -> Optional[str]:
        """
        Get the checkout URL after adding items to cart.
        
        Args:
            domain: The shop domain (e.g., "example.myshopify.com")
            
        Returns:
            The checkout URL if successful, None otherwise
        """
        try:
            logger.info(f"Getting checkout URL for domain: {domain}")
            
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
                checkout_url = response.url
                
                # Extract checkout token if available
                if 'checkouts' in parsed_url.path:
                    checkout_token = parsed_url.path.split('/')[-1]
                    logger.info(f"Found checkout token: {checkout_token}")
                
                logger.info(f"Checkout URL: {checkout_url}")
                return checkout_url
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
                        checkout_url = f"https://{domain}{checkout_path}"
                    else:
                        checkout_url = checkout_path
                        
                    logger.info(f"Found checkout URL from cart: {checkout_url}")
                    return checkout_url
                    
            logger.error("Could not find checkout URL")
            return None
        except Exception as e:
            logger.error(f"Error getting checkout URL: {e}")
            return None

    def extract_form_data(self, html_content: str) -> Dict[str, str]:
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

    def submit_shipping_info(self, checkout_url: str, user_data: Dict[str, str]) -> Optional[str]:
        """
        Submit shipping information to the checkout page.
        
        Args:
            checkout_url: The checkout URL
            user_data: Dictionary containing user shipping information
            
        Returns:
            The URL of the next step if successful, None otherwise
        """
        try:
            # Ensure checkout_url is properly formatted
            if not (checkout_url.startswith('https://') or checkout_url.startswith('http://')):
                checkout_url = f"https://{checkout_url}"
                
            logger.info(f"Submitting shipping info to: {checkout_url}")
            
            # Get the checkout page to extract form data
            checkout_response = self.session.get(checkout_url, timeout=10)
            if checkout_response.status_code != 200:
                logger.error(f"Failed to get checkout page: {checkout_response.status_code}")
                return None
                
            # Extract form data from the page
            form_data = self.extract_form_data(checkout_response.text)
            
            # Add shipping information to form data
            shipping_data = {
                'checkout[email]': user_data.get('email', 'test@example.com'),
                'checkout[shipping_address][first_name]': user_data.get('first_name', 'John'),
                'checkout[shipping_address][last_name]': user_data.get('last_name', 'Doe'),
                'checkout[shipping_address][address1]': user_data.get('address1', '123 Main St'),
                'checkout[shipping_address][address2]': user_data.get('address2', ''),
                'checkout[shipping_address][city]': user_data.get('city', 'New York'),
                'checkout[shipping_address][country]': user_data.get('country', 'United States'),
                'checkout[shipping_address][province]': user_data.get('province', 'New York'),
                'checkout[shipping_address][zip]': user_data.get('zip', '10001'),
                'checkout[shipping_address][phone]': user_data.get('phone', '2125551234'),
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
                'Origin': checkout_url.split('/checkouts')[0],
                'Referer': checkout_url
            }
            
            # Determine the submission URL
            if '/checkouts/' in checkout_url:
                submit_url = checkout_url
            else:
                submit_url = f"{checkout_url}/processing"
                
            shipping_response = self.session.post(
                submit_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=10
            )
            
            # Check if we were redirected to the shipping method page
            if shipping_response.status_code in (200, 302):
                next_url = shipping_response.url
                logger.info(f"Shipping info submitted successfully, next URL: {next_url}")
                return next_url
            else:
                logger.error(f"Failed to submit shipping info: {shipping_response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error submitting shipping info: {e}")
            return None

    def select_shipping_method(self, shipping_url: str) -> Optional[str]:
        """
        Select a shipping method on the shipping page.
        
        Args:
            shipping_url: The shipping method selection page URL
            
        Returns:
            The URL of the next step if successful, None otherwise
        """
        try:
            logger.info(f"Selecting shipping method at: {shipping_url}")
            
            # Get the shipping page to extract available methods
            shipping_response = self.session.get(shipping_url, timeout=10)
            if shipping_response.status_code != 200:
                logger.error(f"Failed to get shipping page: {shipping_response.status_code}")
                return None
                
            # Extract form data from the page
            form_data = self.extract_form_data(shipping_response.text)
            
            # Look for available shipping methods
            shipping_methods = re.findall(r'<input[^>]*name="checkout\[shipping_rate\]\[id\]"[^>]*value="([^"]*)"', shipping_response.text)
            
            if shipping_methods:
                # Select the first available shipping method
                form_data['checkout[shipping_rate][id]'] = shipping_methods[0]
                logger.info(f"Selected shipping method: {shipping_methods[0]}")
            else:
                logger.warning("No shipping methods found, continuing anyway")
                
            # Add step information
            form_data['step'] = 'shipping_method'
            
            # Submit shipping method selection
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': shipping_url.split('/checkouts')[0],
                'Referer': shipping_url
            }
            
            shipping_method_response = self.session.post(
                shipping_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=10
            )
            
            # Check if we were redirected to the payment page
            if shipping_method_response.status_code in (200, 302):
                next_url = shipping_method_response.url
                logger.info(f"Shipping method selected successfully, next URL: {next_url}")
                return next_url
            else:
                logger.error(f"Failed to select shipping method: {shipping_method_response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error selecting shipping method: {e}")
            return None

    def process_payment(self, payment_url: str, cc: str, month: str, year: str, cvv: str) -> Dict[str, Any]:
        """
        Process payment on the payment page.
        
        Args:
            payment_url: The payment page URL
            cc: Credit card number
            month: Expiration month (2 digits)
            year: Expiration year (2 or 4 digits)
            cvv: Card verification value
            
        Returns:
            Dictionary with payment result information
        """
        try:
            logger.info(f"Processing payment at: {payment_url}")
            
            # Get the payment page to extract payment gateway information
            payment_response = self.session.get(payment_url, timeout=10)
            if payment_response.status_code != 200:
                logger.error(f"Failed to get payment page: {payment_response.status_code}")
                return {"status": False, "message": "Failed to access payment page"}
                
            # Extract form data and payment gateway information
            form_data = self.extract_form_data(payment_response.text)
            
            # Determine payment gateway type
            payment_html = payment_response.text
            
            # Check for Shopify Payments (default gateway)
            if 'data-shopify-pay' in payment_html or 'shopify-payment-method' in payment_html:
                return self._process_shopify_payment(payment_url, payment_html, form_data, cc, month, year, cvv)
            
            # Check for Stripe
            elif 'stripe.com' in payment_html:
                return self._process_stripe_payment(payment_url, payment_html, form_data, cc, month, year, cvv)
                
            # Check for PayPal
            elif 'paypal.com' in payment_html:
                return {"status": False, "message": "PayPal checkout not supported in this implementation"}
                
            # Default to generic payment processor
            else:
                return self._process_generic_payment(payment_url, payment_html, form_data, cc, month, year, cvv)
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return {"status": False, "message": f"Payment processing error: {str(e)}"}

    def _process_shopify_payment(self, payment_url: str, payment_html: str, form_data: Dict[str, str], 
                                cc: str, month: str, year: str, cvv: str) -> Dict[str, Any]:
        """
        Process payment using Shopify Payments gateway.
        
        Args:
            payment_url: The payment page URL
            payment_html: HTML content of the payment page
            form_data: Extracted form data
            cc: Credit card number
            month: Expiration month (2 digits)
            year: Expiration year (2 or 4 digits)
            cvv: Card verification value
            
        Returns:
            Dictionary with payment result information
        """
        try:
            logger.info("Processing payment with Shopify Payments gateway")
            
            # Extract payment gateway ID
            gateway_id_match = re.search(r'data-gateway-id="([^"]*)"', payment_html)
            if not gateway_id_match:
                logger.error("Could not find payment gateway ID")
                return {"status": False, "message": "Payment gateway ID not found"}
                
            gateway_id = gateway_id_match.group(1)
            
            # Extract payment session ID
            session_id_match = re.search(r'data-payment-session-id="([^"]*)"', payment_html)
            session_id = session_id_match.group(1) if session_id_match else ""
            
            # Format card data
            if len(year) == 2:
                formatted_year = f"20{year}"
            else:
                formatted_year = year
                
            # Add payment information to form data
            payment_data = {
                'checkout[payment_gateway]': gateway_id,
                'checkout[credit_card][number]': cc,
                'checkout[credit_card][name]': "John Doe",
                'checkout[credit_card][month]': month,
                'checkout[credit_card][year]': formatted_year,
                'checkout[credit_card][verification_value]': cvv,
                'checkout[different_billing_address]': 'false',
                'checkout[remember_me]': 'false',
                'checkout[vault_phone]': 'false',
                'checkout[total_price]': form_data.get('checkout[total_price]', ''),
                'complete': '1',
                'step': 'payment_method'
            }
            
            # Add session ID if available
            if session_id:
                payment_data['checkout[payment_session_id]'] = session_id
                
            # Merge form data with payment data
            form_data.update(payment_data)
            
            # Submit payment
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': payment_url.split('/checkouts')[0],
                'Referer': payment_url
            }
            
            payment_response = self.session.post(
                payment_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=15  # Longer timeout for payment processing
            )
            
            # Parse the payment result
            return self._parse_payment_result(payment_response)
        except Exception as e:
            logger.error(f"Error processing Shopify payment: {e}")
            return {"status": False, "message": f"Shopify payment error: {str(e)}"}

    def _process_stripe_payment(self, payment_url: str, payment_html: str, form_data: Dict[str, str], 
                               cc: str, month: str, year: str, cvv: str) -> Dict[str, Any]:
        """
        Process payment using Stripe gateway.
        
        Args:
            payment_url: The payment page URL
            payment_html: HTML content of the payment page
            form_data: Extracted form data
            cc: Credit card number
            month: Expiration month (2 digits)
            year: Expiration year (2 or 4 digits)
            cvv: Card verification value
            
        Returns:
            Dictionary with payment result information
        """
        logger.info("Stripe payment processing not fully implemented")
        return {"status": False, "message": "Stripe payment processing not fully implemented"}

    def _process_generic_payment(self, payment_url: str, payment_html: str, form_data: Dict[str, str], 
                                cc: str, month: str, year: str, cvv: str) -> Dict[str, Any]:
        """
        Process payment using a generic payment gateway.
        
        Args:
            payment_url: The payment page URL
            payment_html: HTML content of the payment page
            form_data: Extracted form data
            cc: Credit card number
            month: Expiration month (2 digits)
            year: Expiration year (2 or 4 digits)
            cvv: Card verification value
            
        Returns:
            Dictionary with payment result information
        """
        try:
            logger.info("Processing payment with generic payment gateway")
            
            # Extract payment gateway ID if available
            gateway_id_match = re.search(r'name="checkout\[payment_gateway\]"[^>]*value="([^"]*)"', payment_html)
            if gateway_id_match:
                gateway_id = gateway_id_match.group(1)
                form_data['checkout[payment_gateway]'] = gateway_id
            
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
                'complete': '1',
                'step': 'payment_method'
            }
            
            # Merge form data with payment data
            form_data.update(payment_data)
            
            # Submit payment
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': payment_url.split('/checkouts')[0],
                'Referer': payment_url
            }
            
            payment_response = self.session.post(
                payment_url,
                data=form_data,
                headers=headers,
                allow_redirects=True,
                timeout=15  # Longer timeout for payment processing
            )
            
            # Parse the payment result
            return self._parse_payment_result(payment_response)
        except Exception as e:
            logger.error(f"Error processing generic payment: {e}")
            return {"status": False, "message": f"Payment error: {str(e)}"}

    def _parse_payment_result(self, response: requests.Response) -> Dict[str, Any]:
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
                logger.info("Payment successful - redirected to thank you page")
                
                # Try to extract order number
                order_match = re.search(r'order[_-]([a-zA-Z0-9]+)', response.url)
                order_id = order_match.group(1) if order_match else "unknown"
                
                return {
                    "status": True,
                    "result": "Approved - Charged",
                    "message": "Payment successful",
                    "order_id": order_id,
                    "redirect_url": response.url
                }
                
            # Check for 3D Secure redirect
            elif '3d_secure' in response.url or 'cardinal' in response.url or 'authenticate' in response.url:
                logger.info("3D Secure authentication required")
                return {
                    "status": False,
                    "result": "3D Secure Required",
                    "message": "3D Secure authentication required",
                    "redirect_url": response.url
                }
                
            # Check for payment errors in the response content
            content = response.text.lower()
            
            if 'card was declined' in content or 'declined' in content:
                logger.warning("Payment declined")
                return {
                    "status": False,
                    "result": "Declined",
                    "message": "Card was declined"
                }
                
            elif 'invalid' in content and ('card' in content or 'number' in content):
                logger.warning("Invalid card number")
                return {
                    "status": False,
                    "result": "Invalid Card",
                    "message": "Invalid card number"
                }
                
            elif 'expired' in content:
                logger.warning("Expired card")
                return {
                    "status": False,
                    "result": "Expired Card",
                    "message": "Card has expired"
                }
                
            elif 'cvv' in content or 'security code' in content or 'verification value' in content:
                logger.warning("Invalid CVV")
                return {
                    "status": False,
                    "result": "Invalid CVV",
                    "message": "Invalid security code"
                }
                
            # Default to unknown error
            logger.error("Unknown payment result")
            return {
                "status": False,
                "result": "Unknown",
                "message": "Payment processing failed with unknown error"
            }
        except Exception as e:
            logger.error(f"Error parsing payment result: {e}")
            return {
                "status": False,
                "result": "Error",
                "message": f"Error parsing payment result: {str(e)}"
            }

def process_checkout(product_url: str, cc: Optional[str] = None, month: Optional[str] = None, 
                    year: Optional[str] = None, cvv: Optional[str] = None, 
                    custom_proxy: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a complete checkout flow for a Shopify product.
    
    Args:
        product_url: URL of the product to purchase
        cc: Credit card number (optional)
        month: Expiration month (optional)
        year: Expiration year (optional)
        cvv: Card verification value (optional)
        custom_proxy: Optional proxy string
        
    Returns:
        Dictionary with checkout result information
    """
    try:
        # Extract domain from product URL
        parsed_url = urlparse(product_url)
        domain = parsed_url.netloc
        
        # Initialize checkout processor
        checkout = ShopifyCheckout(custom_proxy)
        
        # Step 1: Get product variant ID
        variant_id = checkout.get_product_variant_id(product_url)
        if not variant_id:
            return {"status": False, "message": "Failed to get product variant ID"}
            
        logger.info(f"Found variant ID: {variant_id}")
        
        # Step 2: Add to cart
        add_result = checkout.add_to_cart(domain, variant_id)
        if not add_result:
            return {"status": False, "message": "Failed to add product to cart"}
            
        # Step 3: Get checkout URL
        checkout_url = checkout.get_checkout_url(domain)
        if not checkout_url:
            return {"status": False, "message": "Failed to get checkout URL"}
            
        # If no payment details provided, stop here and return cookies and checkout URL
        if not all([cc, month, year, cvv]):
            cookies_dict = {cookie.name: cookie.value for cookie in checkout.session.cookies}
            return {
                "status": True,
                "message": "Added to cart successfully",
                "cookies": cookies_dict,
                "checkout_url": checkout_url
            }
            
        # Step 4: Submit shipping information
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "address1": "123 Main St",
            "city": "New York",
            "province": "New York",
            "country": "United States",
            "zip": "10001",
            "phone": "2125551234"
        }
        
        shipping_url = checkout.submit_shipping_info(checkout_url, user_data)
        if not shipping_url:
            return {"status": False, "message": "Failed to submit shipping information"}
            
        # Step 5: Select shipping method
        payment_url = checkout.select_shipping_method(shipping_url)
        if not payment_url:
            return {"status": False, "message": "Failed to select shipping method"}
            
        # Step 6: Process payment
        payment_result = checkout.process_payment(payment_url, cc, month, year, cvv)
        
        return payment_result
    except Exception as e:
        logger.error(f"Error in checkout process: {e}")
        return {"status": False, "message": f"Checkout error: {str(e)}"}

# Example usage (for educational purposes only)
if __name__ == "__main__":
    # This is just an example and should not be used for actual checkout automation
    result = process_checkout(
        product_url="https://example.myshopify.com/products/sample-product",
        # Payment details intentionally omitted for security reasons
    )
    
    print(json.dumps(result, indent=2))