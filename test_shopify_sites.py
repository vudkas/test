#!/usr/bin/env python3
"""
Test script for checking Shopify sites and testing checkout process
"""

import sys
import json
import logging
import argparse
import time
from datetime import datetime
from enhanced_shopify_bot import EnhancedShopifyBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("shopify_sites_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_shopify_sites')

def test_site(site_url, proxy=None, card_info=None):
    """Test a Shopify site by finding a product, adding to cart, and checking out"""
    logger.info(f"Testing site: {site_url}")
    
    results = {
        "site": site_url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "product_found": False,
        "add_to_cart": False,
        "checkout_url": None,
        "payment_page": False,
        "card_result": None,
        "thank_you_url": None,
        "error_message": None
    }
    
    try:
        # Initialize the bot
        bot = EnhancedShopifyBot(custom_proxy=proxy)
        
        # First, try to get the homepage to find product links
        logger.info(f"Fetching homepage: {site_url}")
        response = bot.session.get(site_url, timeout=20)
        
        if response.status_code != 200:
            results["error_message"] = f"Failed to access homepage: {response.status_code}"
            logger.error(results["error_message"])
            return results
        
        # Try to find a product URL
        product_url = None
        
        # Method 1: Look for /products/ links
        from bs4 import BeautifulSoup
        import re
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find all links that might be product links
        product_links = []
        
        # Method 1a: Look for /products/ links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/products/' in href or '/product/' in href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = site_url.rstrip('/') + href
                elif not href.startswith('http'):
                    href = site_url.rstrip('/') + '/' + href.lstrip('/')
                product_links.append(href)
        
        # Method 1b: Look for links with product-related text
        if not product_links:
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.text.lower() if link.text else ""
                if text and ('buy' in text or 'add to cart' in text or 'purchase' in text):
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = site_url.rstrip('/') + href
                    elif not href.startswith('http'):
                        href = site_url.rstrip('/') + '/' + href.lstrip('/')
                    product_links.append(href)
        
        # Method 1c: Look for product URLs in the page source
        if not product_links:
            product_patterns = [
                r'href=[\'"]([^\'"]*\/products\/[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]*\/product\/[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]*\/shop\/[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]*\/item\/[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]*\/p\/[^\'"]*)[\'"]'
            ]
            
            for pattern in product_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    # Convert relative URLs to absolute
                    if match.startswith('/'):
                        match = site_url.rstrip('/') + match
                    elif not match.startswith('http'):
                        match = site_url.rstrip('/') + '/' + match.lstrip('/')
                    product_links.append(match)
                
                if product_links:
                    break
        
        if product_links:
            product_url = product_links[0]  # Use the first product link found
            logger.info(f"Found product URL: {product_url}")
        else:
            # If no product links found on homepage, try to find a "shop" or "products" page
            shop_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.text.lower() if link.text else ""
                if text and ('shop' in text or 'product' in text or 'collection' in text or 'store' in text or 'catalog' in text):
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = site_url.rstrip('/') + href
                    elif not href.startswith('http'):
                        href = site_url.rstrip('/') + '/' + href.lstrip('/')
                    shop_links.append(href)
            
            # If no shop links found by text, try by URL pattern
            if not shop_links:
                shop_patterns = [
                    r'href=[\'"]([^\'"]*\/shop[^\'"]*)[\'"]',
                    r'href=[\'"]([^\'"]*\/collections[^\'"]*)[\'"]',
                    r'href=[\'"]([^\'"]*\/catalog[^\'"]*)[\'"]',
                    r'href=[\'"]([^\'"]*\/store[^\'"]*)[\'"]',
                    r'href=[\'"]([^\'"]*\/products[^\'"]*)[\'"]'
                ]
                
                for pattern in shop_patterns:
                    matches = re.findall(pattern, response.text)
                    for match in matches:
                        # Convert relative URLs to absolute
                        if match.startswith('/'):
                            match = site_url.rstrip('/') + match
                        elif not match.startswith('http'):
                            match = site_url.rstrip('/') + '/' + match.lstrip('/')
                        shop_links.append(match)
                    
                    if shop_links:
                        break
            
            if shop_links:
                # Visit the first shop link to find products
                shop_url = shop_links[0]
                logger.info(f"Visiting shop page: {shop_url}")
                
                shop_response = bot.session.get(shop_url, timeout=20)
                if shop_response.status_code == 200:
                    shop_soup = BeautifulSoup(shop_response.text, 'lxml')
                    
                    # Look for product links in the shop page
                    for link in shop_soup.find_all('a', href=True):
                        href = link['href']
                        if '/products/' in href or '/product/' in href:
                            # Convert relative URLs to absolute
                            if href.startswith('/'):
                                href = site_url.rstrip('/') + href
                            elif not href.startswith('http'):
                                href = site_url.rstrip('/') + '/' + href.lstrip('/')
                            product_links.append(href)
                    
                    # If still no product links, try regex patterns
                    if not product_links:
                        for pattern in product_patterns:
                            matches = re.findall(pattern, shop_response.text)
                            for match in matches:
                                # Convert relative URLs to absolute
                                if match.startswith('/'):
                                    match = site_url.rstrip('/') + match
                                elif not match.startswith('http'):
                                    match = site_url.rstrip('/') + '/' + match.lstrip('/')
                                product_links.append(match)
                            
                            if product_links:
                                break
                    
                    if product_links:
                        product_url = product_links[0]
                        logger.info(f"Found product URL from shop page: {product_url}")
        
        if not product_url:
            results["error_message"] = "Could not find any product links"
            logger.error(results["error_message"])
            return results
        
        # Get product information
        product_info = bot.get_product_info(product_url)
        
        if not product_info:
            results["error_message"] = "Failed to get product information"
            logger.error(results["error_message"])
            return results
        
        results["product_found"] = True
        results["product_info"] = {
            "title": product_info.get("title", "Unknown"),
            "price": product_info.get("price", "Unknown"),
            "variant_id": product_info.get("variant_id", "Unknown"),
            "url": product_info.get("url", product_url)
        }
        
        logger.info(f"Product found: {results['product_info']}")
        
        # Add to cart
        add_result = bot.add_to_cart(product_info)
        
        if not add_result:
            results["error_message"] = "Failed to add product to cart"
            logger.error(results["error_message"])
            return results
        
        results["add_to_cart"] = True
        logger.info("Successfully added product to cart")
        
        # Get checkout URL
        checkout_url = bot.get_checkout_url(product_info)
        
        if not checkout_url:
            results["error_message"] = "Failed to get checkout URL"
            logger.error(results["error_message"])
            return results
        
        results["checkout_url"] = checkout_url
        logger.info(f"Checkout URL: {checkout_url}")
        
        # If card info is provided, proceed with checkout
        if card_info:
            # Submit shipping information
            shipping_result = bot.submit_shipping_info()
            
            if not shipping_result:
                results["error_message"] = "Failed to submit shipping information"
                logger.error(results["error_message"])
                return results
            
            logger.info("Successfully submitted shipping information")
            
            # Select shipping method
            shipping_method_result = bot.select_shipping_method()
            
            if not shipping_method_result:
                results["error_message"] = "Failed to select shipping method"
                logger.error(results["error_message"])
                return results
            
            logger.info("Successfully selected shipping method")
            
            # Process payment
            cc_number, cc_month, cc_year, cc_cvv = card_info.split('|')
            
            payment_result = bot.process_payment(cc_number, cc_month, cc_year, cc_cvv)
            
            results["payment_page"] = True
            
            if payment_result:
                results["card_result"] = payment_result
                
                # Check if we have a thank you page URL
                if bot.current_url and 'thank_you' in bot.current_url:
                    results["thank_you_url"] = bot.current_url
                    results["success"] = True
                    logger.info(f"Payment successful! Thank you page: {bot.current_url}")
                else:
                    logger.info(f"Payment result: {payment_result}")
            else:
                results["error_message"] = "Failed to process payment"
                logger.error(results["error_message"])
        else:
            # If no card info, we consider the test successful if we reached the checkout page
            results["success"] = True
            logger.info("Successfully reached checkout page (no payment attempted)")
        
        return results
        
    except Exception as e:
        results["error_message"] = f"Error testing site: {str(e)}"
        logger.error(results["error_message"], exc_info=True)
        return results

def main():
    parser = argparse.ArgumentParser(description='Test Shopify sites')
    parser.add_argument('--sites', nargs='+', help='List of Shopify site URLs to test')
    parser.add_argument('--product-urls', nargs='+', help='List of direct product URLs to test')
    parser.add_argument('--proxy', help='Proxy to use (format: ip:port:user:pass)')
    parser.add_argument('--card', help='Card info to use for checkout (format: number|month|year|cvv)')
    parser.add_argument('--output', default='shopify_sites_test_results.json', help='Output file for results')
    
    args = parser.parse_args()
    
    # Default sites if none provided
    if not args.sites and not args.product_urls:
        args.sites = [
            "https://www.sanrio.com/",
            "https://www.getkeysmart.com/",
            "https://classes.familyeducation.com/",
            "https://shop.goya.com/",
            "https://eu.gear.blizzard.com/",
            "https://shop.newscientist.com/",
            "https://store.bostonglobe.com/",
            "https://eu.shop.callofduty.com/",
            "https://shop.nybooks.com/",
            "https://store.bringatrailer.com/",
            "https://racereadymotorsport.com/",
            "https://www.paperbloom.com/",
            "https://sprecherbrewery.com/",
            "https://tackletech3d.com/",
            "https://beauxartsmiami.org/"
        ]
    
    # Known product URLs for specific sites
    known_product_urls = {
        "https://www.sanrio.com/": "https://www.sanrio.com/products/hello-kitty-plush-keychain-red-bow",
        "https://www.getkeysmart.com/": "https://www.getkeysmart.com/products/keysmart-classic-extended-black",
        "https://classes.familyeducation.com/": "https://classes.familyeducation.com/products/the-ultimate-guide-to-homeschooling-teens",
        "https://shop.goya.com/": "https://shop.goya.com/products/goya-adobo-all-purpose-seasoning-with-pepper-8-oz",
        "https://eu.gear.blizzard.com/": "https://eu.gear.blizzard.com/products/world-of-warcraft-sylvanas-windrunner-premium-statue",
        "https://shop.newscientist.com/": "https://shop.newscientist.com/products/new-scientist-magazine-subscription",
        "https://store.bostonglobe.com/": "https://store.bostonglobe.com/products/boston-globe-digital-subscription",
        "https://eu.shop.callofduty.com/": "https://eu.shop.callofduty.com/products/call-of-duty-modern-warfare-iii-t-shirt",
        "https://shop.nybooks.com/": "https://shop.nybooks.com/products/new-york-review-of-books-subscription",
        "https://store.bringatrailer.com/": "https://store.bringatrailer.com/products/bat-logo-hat"
    }
    
    # Default card if none provided
    if not args.card:
        args.card = "5577557193296184|05|2026|620"
    
    results = []
    
    # Process sites
    if args.sites:
        for site in args.sites:
            logger.info(f"Testing site: {site}")
            
            # If we have a known product URL for this site, use it directly
            if site in known_product_urls:
                logger.info(f"Using known product URL for {site}: {known_product_urls[site]}")
                product_info = EnhancedShopifyBot(custom_proxy=args.proxy).get_product_info(known_product_urls[site])
                if product_info:
                    logger.info(f"Successfully fetched product info from known URL")
                    site_result = test_site(site, args.proxy, args.card)
                else:
                    logger.info(f"Failed to fetch product info from known URL, falling back to site discovery")
                    site_result = test_site(site, args.proxy, args.card)
            else:
                site_result = test_site(site, args.proxy, args.card)
                
            results.append(site_result)
            
            # Save results after each site test
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Wait a bit between sites to avoid rate limiting
            time.sleep(5)
    
    # Process direct product URLs if provided
    if args.product_urls:
        for product_url in args.product_urls:
            logger.info(f"Testing product URL: {product_url}")
            
            # Extract site URL from product URL
            from urllib.parse import urlparse
            parsed_url = urlparse(product_url)
            site_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            
            # Initialize bot and get product info directly
            bot = EnhancedShopifyBot(custom_proxy=args.proxy)
            product_info = bot.get_product_info(product_url)
            
            if product_info:
                logger.info(f"Successfully fetched product info")
                
                # Add to cart
                add_result = bot.add_to_cart(product_info)
                
                if add_result:
                    logger.info(f"Successfully added product to cart")
                    
                    # Get checkout URL
                    checkout_url = bot.get_checkout_url(product_info)
                    
                    if checkout_url:
                        logger.info(f"Successfully got checkout URL: {checkout_url}")
                        
                        # If card info is provided, proceed with checkout
                        if args.card:
                            # Submit shipping information
                            shipping_result = bot.submit_shipping_info()
                            
                            if shipping_result:
                                logger.info(f"Successfully submitted shipping info")
                                
                                # Select shipping method
                                shipping_method_result = bot.select_shipping_method()
                                
                                if shipping_method_result:
                                    logger.info(f"Successfully selected shipping method")
                                    
                                    # Process payment
                                    cc_number, cc_month, cc_year, cc_cvv = args.card.split('|')
                                    payment_result = bot.process_payment(cc_number, cc_month, cc_year, cc_cvv)
                                    
                                    result = {
                                        "site": site_url,
                                        "product_url": product_url,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "success": True,
                                        "product_found": True,
                                        "add_to_cart": True,
                                        "checkout_url": checkout_url,
                                        "payment_page": True,
                                        "card_result": payment_result,
                                        "thank_you_url": bot.payment_url if bot.payment_url and 'thank_you' in bot.payment_url else None,
                                        "error_message": None
                                    }
                                else:
                                    result = {
                                        "site": site_url,
                                        "product_url": product_url,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "success": False,
                                        "product_found": True,
                                        "add_to_cart": True,
                                        "checkout_url": checkout_url,
                                        "payment_page": False,
                                        "card_result": None,
                                        "thank_you_url": None,
                                        "error_message": "Failed to select shipping method"
                                    }
                            else:
                                result = {
                                    "site": site_url,
                                    "product_url": product_url,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "success": False,
                                    "product_found": True,
                                    "add_to_cart": True,
                                    "checkout_url": checkout_url,
                                    "payment_page": False,
                                    "card_result": None,
                                    "thank_you_url": None,
                                    "error_message": "Failed to submit shipping information"
                                }
                        else:
                            result = {
                                "site": site_url,
                                "product_url": product_url,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "success": True,
                                "product_found": True,
                                "add_to_cart": True,
                                "checkout_url": checkout_url,
                                "payment_page": False,
                                "card_result": None,
                                "thank_you_url": None,
                                "error_message": None
                            }
                    else:
                        result = {
                            "site": site_url,
                            "product_url": product_url,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "success": False,
                            "product_found": True,
                            "add_to_cart": True,
                            "checkout_url": None,
                            "payment_page": False,
                            "card_result": None,
                            "thank_you_url": None,
                            "error_message": "Failed to get checkout URL"
                        }
                else:
                    result = {
                        "site": site_url,
                        "product_url": product_url,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "success": False,
                        "product_found": True,
                        "add_to_cart": False,
                        "checkout_url": None,
                        "payment_page": False,
                        "card_result": None,
                        "thank_you_url": None,
                        "error_message": "Failed to add product to cart"
                    }
            else:
                result = {
                    "site": site_url,
                    "product_url": product_url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "success": False,
                    "product_found": False,
                    "add_to_cart": False,
                    "checkout_url": None,
                    "payment_page": False,
                    "card_result": None,
                    "thank_you_url": None,
                    "error_message": "Failed to get product information"
                }
            
            results.append(result)
            
            # Save results after each product test
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Wait a bit between products to avoid rate limiting
            time.sleep(5)
        
        # Save results after each site test
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Wait a bit between sites to avoid rate limiting
        time.sleep(5)
    
    logger.info(f"Testing complete. Results saved to {args.output}")
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Summary: {success_count}/{len(results)} sites successfully tested")
    
    for result in results:
        status = "✅ Success" if result["success"] else "❌ Failed"
        error = f" - {result['error_message']}" if result["error_message"] else ""
        logger.info(f"{result['site']}: {status}{error}")

if __name__ == "__main__":
    main()