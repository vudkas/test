import sys
import json
import time
import re
from main import ShopifyPaymentProcessor

def test_shopify_checkout(url, cc=None, month=None, year=None, cvv=None):
    """
    Test the Shopify checkout process for a given URL
    If card details are not provided, it will only test adding to cart and extracting cookies
    
    Note: This site is protected by hCaptcha, which requires browser automation to solve.
    For a complete checkout test, use the browser_checkout.py script with a captcha solver.
    """
    print("⚠️ Warning: This site may be protected by hCaptcha or Cloudflare.")
    print("For a complete checkout test, use the browser_checkout.py script with a captcha solver.")
    print(f"Testing checkout for: {url}")
    
    # Initialize the processor
    processor = ShopifyPaymentProcessor()
    
    # Extract domain from URL
    domain_match = re.match(r'https?://([^/]+)', url)
    if domain_match:
        domain = domain_match.group(1)
    else:
        domain = "klaritylifestyle.com"
    
    # Set up additional headers to help with Cloudflare
    processor.session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': url,
        'Host': domain,
        'Origin': f"https://{domain}",
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Connection': 'keep-alive'
    })
    
    # Step 1: Visit the product page
    try:
        print("Visiting product page...")
        response = processor.session.get(url)
        
        # Check for Cloudflare or hCaptcha
        if "cloudflare" in response.text.lower() or "cf-" in response.text.lower():
            print("⚠️ Cloudflare protection detected!")
            print("This requires browser automation to solve. Cannot proceed with simple requests.")
            return {"status": False, "message": "Cloudflare protection detected"}
            
        if "hcaptcha" in response.text.lower():
            print("⚠️ hCaptcha protection detected!")
            print("This requires browser automation to solve. Cannot proceed with simple requests.")
            return {"status": False, "message": "hCaptcha protection detected"}
            
        print(f"Response status code: {response.status_code}")
        
        # Initialize variables
        title = None
        price = None
        variant_id = None
        
        # Extract product information from JSON data in the page
        # This is more reliable for Shopify sites
        product_json_match = re.search(r'var\s+meta\s*=\s*({.*?});', response.text, re.DOTALL)
        if not product_json_match:
            product_json_match = re.search(r'({.*?"variants":\s*\[.*?\].*?})', response.text, re.DOTALL)
            
        if product_json_match:
            try:
                # Clean up the JSON string - sometimes it has JavaScript comments or trailing commas
                json_str = product_json_match.group(1)
                # Remove JavaScript comments
                json_str = re.sub(r'\/\/.*?$', '', json_str, flags=re.MULTILINE)
                # Fix trailing commas in arrays and objects
                json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
                
                # Try to parse the JSON
                product_data = json.loads(json_str)
                
                # Extract product info
                if "product" in product_data:
                    product = product_data["product"]
                    title = product.get("title", "Unknown Product")
                    
                    # Get the first variant
                    if "variants" in product and len(product["variants"]) > 0:
                        variant = product["variants"][0]
                        variant_id = str(variant.get("id", ""))
                        price_cents = variant.get("price", 0)
                        price = f"${price_cents/100:.2f}" if price_cents > 100 else f"${price_cents:.2f}"
                        
                        print(f"Product: {title}")
                        print(f"Price: {price}")
                        print(f"Variant ID: {variant_id}")
                    else:
                        print("No variants found in product data")
            except json.JSONDecodeError as e:
                print(f"Error parsing product JSON: {e}")
                
        # If we couldn't extract from JSON, try regex patterns
        if not variant_id:
            # Try to find variant ID in the page
            variant_patterns = [
                r'"id":(\d+),"title":"[^"]+","option1":"[^"]+","option2"',
                r'"id":(\d+),"title":"[^"]+"',
                r'variant_id[\'"]?\s*:\s*[\'"]?(\d+)[\'"]?',
                r'variantId[\'"]?\s*:\s*[\'"]?(\d+)[\'"]?',
                r'ProductSelect[\'"]?.*?value=[\'"]?(\d+)[\'"]?',
                r'product-variant-id[\'"]?\s*:\s*[\'"]?(\d+)[\'"]?',
                r'data-variant-id=[\'"]?(\d+)[\'"]?',
                r'name="id"\s+value="(\d+)"'
            ]
            
            for pattern in variant_patterns:
                variant_match = re.search(pattern, response.text)
                if variant_match:
                    variant_id = variant_match.group(1)
                    print(f"Found variant ID using regex: {variant_id}")
                    break
        
        # If we still don't have a variant ID, try one more approach
        if not variant_id:
            # Look for a select element with options containing variant IDs
            select_match = re.search(r'<select[^>]*id="ProductSelect"[^>]*>(.*?)</select>', response.text, re.DOTALL)
            if select_match:
                select_content = select_match.group(1)
                option_match = re.search(r'<option[^>]*value="(\d+)"', select_content)
                if option_match:
                    variant_id = option_match.group(1)
                    print(f"Found variant ID from select options: {variant_id}")
        
        # If we still don't have a variant ID, try to extract from the JSON data in the page
        if not variant_id:
            # Look for productVariants in the web-pixels-manager-setup script
            pixels_match = re.search(r'"productVariants":\[(.*?)\]', response.text, re.DOTALL)
            if pixels_match:
                variants_json = pixels_match.group(1)
                # Try to find all variant IDs
                variant_id_matches = re.findall(r'"id":"?(\d+)"?', variants_json)
                if variant_id_matches:
                    variant_id = variant_id_matches[0]  # Use the first variant
                    print(f"Found variant ID from web pixels data: {variant_id}")
                    print(f"Available variants: {variant_id_matches}")
                    
            # If still not found, try another approach with initData
            if not variant_id:
                init_data_match = re.search(r'initData:\s*({.*?}),\s*},', response.text, re.DOTALL)
                if init_data_match:
                    try:
                        init_data_str = init_data_match.group(1)
                        # Clean up the string for JSON parsing
                        init_data_str = re.sub(r',\s*([\]}])', r'\1', init_data_str)
                        # Try to parse as JSON
                        init_data = json.loads(init_data_str)
                        if "productVariants" in init_data and len(init_data["productVariants"]) > 0:
                            variant_id = str(init_data["productVariants"][0]["id"])
                            print(f"Found variant ID from initData: {variant_id}")
                    except Exception as e:
                        print(f"Error parsing initData: {e}")
                        
            # Direct extraction as a last resort
            if not variant_id:
                # Try to directly extract from the HTML
                direct_match = re.search(r'id="ProductSelect".*?value="(\d+)"', response.text, re.DOTALL)
                if direct_match:
                    variant_id = direct_match.group(1)
                    print(f"Found variant ID from direct HTML extraction: {variant_id}")
                    
                # Try to find it in the meta tag
                if not variant_id:
                    meta_match = re.search(r'variantId":(\d+)', response.text)
                    if meta_match:
                        variant_id = meta_match.group(1)
                        print(f"Found variant ID from meta tag: {variant_id}")
                        
                # Try to find it in the product JSON
                if not variant_id:
                    json_match = re.search(r'"variants":\[{"id":(\d+)', response.text)
                    if json_match:
                        variant_id = json_match.group(1)
                        print(f"Found variant ID from product JSON: {variant_id}")
                        
                # Hardcoded extraction for this specific product
                if not variant_id and "power-stripe-skirt" in url:
                    variant_id = "30322225152139"  # X-SMALL variant
                    print(f"Using hardcoded variant ID for Power Stripe Skirt: {variant_id}")
        
        if not variant_id:
            print("❌ Could not find variant ID. Cannot proceed with checkout.")
            return {"status": False, "message": "No variant ID found"}
            
        # Step 2: Add to cart
        print("\nAdding to cart...")
        cart_result = processor.add_to_cart(domain, variant_id)
        print(f"Add to cart result: {cart_result['success']}")
        
        if not cart_result['success']:
            print("❌ Failed to add to cart. Cannot proceed with checkout.")
            return {"status": False, "message": "Failed to add to cart"}
            
        # Step 3: Extract cookies
        print("\nExtracted cookies:")
        cookies_dict = processor.session.cookies.get_dict()
        for key, value in cookies_dict.items():
            print(f"{key}: {value}")
            
        # Step 4: Get checkout URL
        print("\nGetting checkout URL...")
        checkout_url = processor.get_checkout_url(domain)
        print(f"Checkout URL: {checkout_url}")
        
        if not checkout_url:
            # Try an alternative approach - directly go to the checkout page
            print("Trying alternative checkout approach...")
            try:
                checkout_response = processor.session.get(f"https://{domain}/checkout")
                if 'checkouts/' in checkout_response.url:
                    checkout_url = checkout_response.url.split('https://')[1]
                    print(f"Found checkout URL from direct navigation: {checkout_url}")
                else:
                    # Try to extract from cart page
                    cart_response = processor.session.get(f"https://{domain}/cart")
                    checkout_link = re.search(r'href="([^"]*\/checkout[^"]*)"', cart_response.text)
                    if checkout_link:
                        checkout_path = checkout_link.group(1)
                        if checkout_path.startswith('http'):
                            checkout_url = checkout_path.split('https://')[1]
                        else:
                            checkout_url = f"{domain}{checkout_path}"
                        print(f"Found checkout URL from cart page: {checkout_url}")
            except Exception as e:
                print(f"Alternative checkout approach failed: {e}")
                
        if not checkout_url:
            print("❌ Failed to get checkout URL. Cannot proceed with checkout.")
            return {"status": False, "message": "Failed to get checkout URL"}
            
        # If no card details provided, stop here
        if not all([cc, month, year, cvv]):
            print("\n✅ Successfully added to cart and extracted cookies.")
            print("Card details not provided, so stopping before payment processing.")
            return {
                "status": True, 
                "message": "Added to cart successfully", 
                "cookies": cookies_dict,
                "checkout_url": checkout_url
            }
            
        # Step 5: Submit shipping info
        print("\nSubmitting shipping information...")
        user_data = processor.get_user_data()
        shipping_result = processor.submit_shipping_info(checkout_url, user_data)
        print(f"Shipping submission result: {shipping_result['success']}")
        
        if not shipping_result['success']:
            print("❌ Failed to submit shipping information. Cannot proceed with checkout.")
            return {"status": False, "message": "Failed to submit shipping information"}
            
        # Step 6: Process payment
        print("\nProcessing payment...")
        payment_result = processor.process_card_payment(
            checkout_url, 
            domain, 
            cc, 
            month, 
            year, 
            cvv, 
            user_data
        )
        
        print("\nPayment Result:")
        print(json.dumps(payment_result, indent=2))
        
        return payment_result
        
    except Exception as e:
        print(f"❌ Error during checkout process: {str(e)}")
        return {"status": False, "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://klaritylifestyle.com/products/power-stripe-skirt"
    
    # Test with just the URL (no payment processing)
    result = test_shopify_checkout(url)
    
    # If you want to test with a card, uncomment and modify the following line:
    # result = test_shopify_checkout(url, "4111111111111111", "01", "2025", "123")