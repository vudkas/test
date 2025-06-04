import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def test_shopify_checkout(url, cc=None, month=None, year=None, cvv=None):
    """
    Test the Shopify checkout process using a browser
    If card details are not provided, it will only test adding to cart and extracting cookies
    """
    print(f"Testing checkout for: {url}")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Initialize the browser
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Step 1: Visit the product page
        print("Visiting product page...")
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for Cloudflare or hCaptcha
        page_source = driver.page_source.lower()
        if "cloudflare" in page_source or "cf-" in page_source:
            print("⚠️ Cloudflare protection detected!")
            print("Waiting for Cloudflare to resolve (30 seconds)...")
            time.sleep(30)  # Wait for Cloudflare to resolve
            
        if "hcaptcha" in page_source:
            print("⚠️ hCaptcha protection detected!")
            print("Waiting for hCaptcha to resolve (30 seconds)...")
            time.sleep(30)  # Wait for hCaptcha to resolve
        
        # Extract product information
        try:
            product_title = driver.find_element(By.CSS_SELECTOR, "h1.product-single__title").text
        except NoSuchElementException:
            try:
                product_title = driver.find_element(By.CSS_SELECTOR, "h1").text
            except NoSuchElementException:
                product_title = "Unknown Product"
        
        print(f"Product: {product_title}")
        
        # Find and select a variant if available
        try:
            # Look for size/variant selector
            variant_selector = driver.find_element(By.CSS_SELECTOR, "select#ProductSelect")
            print("Found variant selector")
        except NoSuchElementException:
            print("No variant selector found, using default variant")
        
        # Step 2: Add to cart
        print("\nAdding to cart...")
        try:
            # Find the Add to Cart button
            add_to_cart_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[name='add'], button.add-to-cart, input[name='add'], button.product-form__cart-submit"))
            )
            add_to_cart_button.click()
            
            # Wait for the cart to update
            time.sleep(3)
            
            print("Successfully added to cart")
        except Exception as e:
            print(f"Failed to add to cart: {e}")
            driver.quit()
            return {"status": False, "message": f"Failed to add to cart: {str(e)}"}
        
        # Step 3: Extract cookies
        print("\nExtracted cookies:")
        cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        for key, value in cookies_dict.items():
            print(f"{key}: {value}")
        
        # Step 4: Go to checkout
        print("\nGoing to checkout...")
        try:
            # Try to find a checkout button
            checkout_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.checkout-button, button.checkout-button, a[href='/checkout'], button[name='checkout']"))
            )
            checkout_button.click()
            
            # Wait for the checkout page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.main__content, div.step"))
            )
            
            checkout_url = driver.current_url
            print(f"Checkout URL: {checkout_url}")
        except Exception as e:
            print(f"Failed to go to checkout: {e}")
            # Try navigating directly to the checkout page
            try:
                driver.get(f"{driver.current_url.split('/cart')[0]}/checkout")
                time.sleep(3)
                checkout_url = driver.current_url
                print(f"Direct navigation to checkout: {checkout_url}")
            except Exception as e2:
                print(f"Failed to navigate to checkout: {e2}")
                driver.quit()
                return {"status": False, "message": f"Failed to go to checkout: {str(e)}"}
        
        # If no card details provided, stop here
        if not all([cc, month, year, cvv]):
            print("\n✅ Successfully added to cart and reached checkout page.")
            print("Card details not provided, so stopping before payment processing.")
            driver.quit()
            return {
                "status": True, 
                "message": "Added to cart successfully", 
                "cookies": cookies_dict,
                "checkout_url": checkout_url
            }
        
        # Step 5: Fill in shipping information
        print("\nFilling shipping information...")
        try:
            # Fill email
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#checkout_email, input[name='checkout[email]']"))
            )
            email_field.send_keys("raven.usu@gmail.com")
            
            # Fill shipping address
            try:
                # First name
                first_name_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_shipping_address_first_name, input[name='checkout[shipping_address][first_name]']")
                first_name_field.send_keys("John")
                
                # Last name
                last_name_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_shipping_address_last_name, input[name='checkout[shipping_address][last_name]']")
                last_name_field.send_keys("Doe")
                
                # Address
                address_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_shipping_address_address1, input[name='checkout[shipping_address][address1]']")
                address_field.send_keys("123 Main St")
                
                # City
                city_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_shipping_address_city, input[name='checkout[shipping_address][city]']")
                city_field.send_keys("New York")
                
                # Zip/Postal code
                zip_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_shipping_address_zip, input[name='checkout[shipping_address][zip]']")
                zip_field.send_keys("10001")
                
                # Try to select country if dropdown exists
                try:
                    country_select = driver.find_element(By.CSS_SELECTOR, "select#checkout_shipping_address_country, select[name='checkout[shipping_address][country]']")
                    # Select United States
                    from selenium.webdriver.support.ui import Select
                    Select(country_select).select_by_visible_text("United States")
                except NoSuchElementException:
                    print("Country dropdown not found, using default")
                
                # Try to select state/province if dropdown exists
                try:
                    state_select = driver.find_element(By.CSS_SELECTOR, "select#checkout_shipping_address_province, select[name='checkout[shipping_address][province]']")
                    # Select New York
                    from selenium.webdriver.support.ui import Select
                    Select(state_select).select_by_visible_text("New York")
                except NoSuchElementException:
                    print("State dropdown not found, using default")
                
                # Phone
                phone_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_shipping_address_phone, input[name='checkout[shipping_address][phone]']")
                phone_field.send_keys("2125551234")
                
                print("Shipping information filled successfully")
            except Exception as e:
                print(f"Error filling shipping address: {e}")
            
            # Continue to shipping method
            try:
                continue_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button#continue_button, button[name='button']"))
                )
                continue_button.click()
                
                # Wait for shipping method page
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.section--shipping-method, div.section--shipping-rate"))
                )
                
                print("Continued to shipping method")
            except Exception as e:
                print(f"Error continuing to shipping method: {e}")
            
            # Continue to payment method
            try:
                continue_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button#continue_button, button[name='button']"))
                )
                continue_button.click()
                
                # Wait for payment method page
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.section--payment-method, div#checkout_payment_gateway_"))
                )
                
                print("Continued to payment method")
            except Exception as e:
                print(f"Error continuing to payment method: {e}")
            
            # Step 6: Fill in payment information
            print("\nFilling payment information...")
            try:
                # Check if there's an iframe for credit card
                try:
                    # Wait for iframe to be available
                    iframe = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.card-fields-iframe"))
                    )
                    
                    # Switch to the iframe
                    driver.switch_to.frame(iframe)
                    
                    # Fill card number
                    card_number_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input#number, input.card-number"))
                    )
                    card_number_field.send_keys(cc)
                    
                    # Switch back to main content
                    driver.switch_to.default_content()
                    
                    # Find name on card iframe
                    name_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id*='name']")
                    driver.switch_to.frame(name_iframe)
                    
                    # Fill name on card
                    name_field = driver.find_element(By.CSS_SELECTOR, "input#name, input.card-name")
                    name_field.send_keys("John Doe")
                    
                    # Switch back to main content
                    driver.switch_to.default_content()
                    
                    # Find expiry iframe
                    expiry_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id*='expiry']")
                    driver.switch_to.frame(expiry_iframe)
                    
                    # Fill expiry
                    expiry_field = driver.find_element(By.CSS_SELECTOR, "input#expiry, input.card-expiry")
                    expiry_field.send_keys(f"{month}{year}")
                    
                    # Switch back to main content
                    driver.switch_to.default_content()
                    
                    # Find CVV iframe
                    cvv_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id*='verification_value']")
                    driver.switch_to.frame(cvv_iframe)
                    
                    # Fill CVV
                    cvv_field = driver.find_element(By.CSS_SELECTOR, "input#verification_value, input.card-cvv")
                    cvv_field.send_keys(cvv)
                    
                    # Switch back to main content
                    driver.switch_to.default_content()
                    
                    print("Payment information filled in iframes")
                except Exception as iframe_error:
                    print(f"Error with iframe payment fields: {iframe_error}")
                    
                    # Try direct input fields
                    try:
                        # Fill card number
                        card_number_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_credit_card_number, input[name='credit_card[number]']")
                        card_number_field.send_keys(cc)
                        
                        # Fill name on card
                        name_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_credit_card_name, input[name='credit_card[name]']")
                        name_field.send_keys("John Doe")
                        
                        # Fill expiry month
                        month_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_credit_card_month, input[name='credit_card[month]']")
                        month_field.send_keys(month)
                        
                        # Fill expiry year
                        year_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_credit_card_year, input[name='credit_card[year]']")
                        year_field.send_keys(year)
                        
                        # Fill CVV
                        cvv_field = driver.find_element(By.CSS_SELECTOR, "input#checkout_credit_card_verification_value, input[name='credit_card[verification_value]']")
                        cvv_field.send_keys(cvv)
                        
                        print("Payment information filled in direct fields")
                    except Exception as direct_error:
                        print(f"Error with direct payment fields: {direct_error}")
                
                # Complete order
                try:
                    complete_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#continue_button, button[type='submit']"))
                    )
                    complete_button.click()
                    
                    # Wait for order processing
                    time.sleep(5)
                    
                    # Check for success or error
                    if "thank_you" in driver.current_url or "order-status" in driver.current_url:
                        print("\n✅ Order completed successfully!")
                        return {
                            "status": True,
                            "result": "Approved - Charged",
                            "message": "Payment successful",
                            "gateway": "Shopify"
                        }
                    else:
                        # Check for error messages
                        try:
                            error_message = driver.find_element(By.CSS_SELECTOR, "div.notice--error, p.notice__text, div.error").text
                            print(f"\n❌ Payment error: {error_message}")
                            
                            # Check if it's a CVV error (which means card is valid)
                            if "CVV" in error_message or "security code" in error_message.lower():
                                return {
                                    "status": True,
                                    "result": "Approved - CVV",
                                    "message": error_message,
                                    "gateway": "Shopify"
                                }
                            # Check if it's an AVS error (which means card is valid)
                            elif "address" in error_message.lower() and "verification" in error_message.lower():
                                return {
                                    "status": True,
                                    "result": "Approved - AVS",
                                    "message": error_message,
                                    "gateway": "Shopify"
                                }
                            # Check if it's an insufficient funds error (which means card is valid)
                            elif "insufficient" in error_message.lower() or "funds" in error_message.lower():
                                return {
                                    "status": True,
                                    "result": "Approved - Insufficient Funds",
                                    "message": error_message,
                                    "gateway": "Shopify"
                                }
                            else:
                                return {
                                    "status": False,
                                    "result": "Declined",
                                    "message": error_message,
                                    "gateway": "Shopify"
                                }
                        except NoSuchElementException:
                            return {
                                "status": False,
                                "result": "Unknown",
                                "message": "Could not determine payment result",
                                "gateway": "Shopify"
                            }
                except Exception as complete_error:
                    print(f"Error completing order: {complete_error}")
                    return {
                        "status": False,
                        "result": "Error",
                        "message": f"Error completing order: {str(complete_error)}",
                        "gateway": "Shopify"
                    }
            except Exception as payment_error:
                print(f"Error with payment process: {payment_error}")
                return {
                    "status": False,
                    "result": "Error",
                    "message": f"Error with payment process: {str(payment_error)}",
                    "gateway": "Shopify"
                }
        except Exception as shipping_error:
            print(f"Error with shipping information: {shipping_error}")
            return {
                "status": False,
                "result": "Error",
                "message": f"Error with shipping information: {str(shipping_error)}",
                "gateway": "Shopify"
            }
    except Exception as e:
        print(f"❌ Error during checkout process: {str(e)}")
        return {"status": False, "message": f"Error: {str(e)}"}
    finally:
        # Always quit the driver to clean up resources
        driver.quit()

if __name__ == "__main__":
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://klaritylifestyle.com/products/power-stripe-skirt"
    
    # Test with just the URL (no payment processing)
    result = test_shopify_checkout(url)
    
    # If you want to test with a card, uncomment and modify the following line:
    # result = test_shopify_checkout(url, "4111111111111111", "01", "2025", "123")
    
    print("\nFinal Result:")
    print(json.dumps(result, indent=2))