#!/usr/bin/env python3
"""
Test script for checking Shopify sites with credit card checkout
"""

import sys
import json
import logging
import argparse
import time
from datetime import datetime
from enhanced_shopify_bot_v2 import EnhancedShopifyBotV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("card_checkout_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_card_checkout')

def test_card(site_url, card_info, proxy=None):
    """Test a credit card on a Shopify site"""
    logger.info(f"Testing card {card_info} on site: {site_url}")
    
    results = {
        "site": site_url,
        "card": card_info,
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
        # Parse card info
        cc_number, cc_month, cc_year, cc_cvv = card_info.split('|')
        
        # Initialize the bot
        bot = EnhancedShopifyBotV2(custom_proxy=proxy)
        
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
                
                # If we found shop links, we're good to go
            
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
        payment_result = bot.process_payment(cc_number, cc_month, cc_year, cc_cvv)
        
        results["payment_page"] = True
        results["card_result"] = payment_result
        
        if payment_result.get("success", False):
            results["success"] = True
            results["thank_you_url"] = payment_result.get("thank_you_url")
            logger.info(f"Payment successful! Thank you page: {results['thank_you_url']}")
        else:
            results["error_message"] = payment_result.get("error", "Unknown payment error")
            logger.error(f"Payment failed: {results['error_message']}")
        
        return results
        
    except Exception as e:
        results["error_message"] = f"Error testing card: {str(e)}"
        logger.error(results["error_message"], exc_info=True)
        return results

def main():
    parser = argparse.ArgumentParser(description='Test credit cards on Shopify sites')
    parser.add_argument('--sites', nargs='+', help='List of Shopify site URLs to test')
    parser.add_argument('--cards', nargs='+', help='List of card info to test (format: number|month|year|cvv)')
    parser.add_argument('--proxy', help='Proxy to use (format: ip:port:user:pass)')
    parser.add_argument('--output', default='card_test_results.json', help='Output file for results')
    
    args = parser.parse_args()
    
    # Default sites if none provided
    if not args.sites:
        args.sites = [
            "https://klaritylifestyle.com/",
            "https://www.sanrio.com/",
            "https://www.getkeysmart.com/",
            "https://classes.familyeducation.com/",
            "https://shop.goya.com/",
            "https://eu.gear.blizzard.com/",
            "https://shop.newscientist.com/",
            "https://store.bostonglobe.com/",
            "https://eu.shop.callofduty.com/",
            "https://shop.nybooks.com/",
            "https://store.bringatrailer.com/"
        ]
    
    # Default cards if none provided
    if not args.cards:
        args.cards = [
            "5577557193296184|05|2026|620",
            "5395937416657109|05|2026|364",
            "4895040589255203|12|2027|410",
            "5509890034510718|06|2028|788"
        ]
    
    results = []
    
    # Test each site with each card
    for site in args.sites:
        for card in args.cards:
            logger.info(f"Testing site: {site} with card: {card}")
            site_result = test_card(site, card, args.proxy)
            results.append(site_result)
            
            # Save results after each test
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Wait a bit between tests to avoid rate limiting
            time.sleep(10)
    
    logger.info(f"Testing complete. Results saved to {args.output}")
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Summary: {success_count}/{len(results)} tests successful")
    
    for result in results:
        status = "✅ Success" if result["success"] else "❌ Failed"
        error = f" - {result['error_message']}" if result["error_message"] else ""
        logger.info(f"{result['site']} with card {result['card']}: {status}{error}")

if __name__ == "__main__":
    main()