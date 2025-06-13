#!/usr/bin/env python3
"""
Debug script to test product fetching functionality
"""

import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def fetch_product_info(url):
    """
    Fetch product information from a Shopify product URL.
    
    Args:
        url: URL of the product page
        
    Returns:
        Dictionary with product information including variants
    """
    print(f"Fetching product information from: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
    
    try:
        response = session.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to get product page: {response.status_code}")
            return None
            
        # Save the HTML response for debugging
        with open("product_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"Response status code: {response.status_code}")
        print(f"Response length: {len(response.text)} bytes")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract product title
        product_title = None
        title_elem = soup.select_one('h1.product-single__title, h1.product__title, h1')
        if title_elem:
            product_title = title_elem.text.strip()
            print(f"Found product title: {product_title}")
        else:
            print("Could not find product title")
            
            # Try to find any h1 tags
            h1_tags = soup.find_all('h1')
            print(f"Found {len(h1_tags)} h1 tags:")
            for h1 in h1_tags:
                print(f"  - {h1.text.strip()}")
        
        # Extract product price
        product_price = None
        price_elem = soup.select_one('[data-product-price], .price__current, .product__price')
        if price_elem:
            price_text = price_elem.text.strip()
            # Extract digits and decimal point from price text
            price_match = re.search(r'[\d,.]+', price_text)
            if price_match:
                product_price = price_match.group(0).replace(',', '')
                print(f"Found product price: {product_price}")
        else:
            print("Could not find product price")
            
            # Try to find any elements with 'price' in their class or id
            price_elems = soup.select('[class*="price"], [id*="price"]')
            print(f"Found {len(price_elems)} elements with 'price' in class/id:")
            for elem in price_elems[:5]:  # Show only first 5 to avoid too much output
                print(f"  - {elem.text.strip()}")
        
        # Extract product variants
        variants = []
        
        # Method 1: Look for variants in JSON data
        json_match = re.search(r'var\s+meta\s*=\s*({.*?});', response.text, re.DOTALL) or \
                     re.search(r'window\.meta\s*=\s*({.*?});', response.text, re.DOTALL) or \
                     re.search(r'var\s+product\s*=\s*({.*?});', response.text, re.DOTALL)
                     
        if json_match:
            print("Found product JSON data")
            try:
                product_json = json.loads(json_match.group(1))
                print(f"Parsed JSON data: {json.dumps(product_json, indent=2)[:500]}...")
                
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
            except json.JSONDecodeError as e:
                print(f"Error parsing product JSON: {e}")
        else:
            print("Could not find product JSON data")
            
            # Try to find any JSON data in script tags
            script_tags = soup.find_all('script', type='application/json')
            print(f"Found {len(script_tags)} script tags with JSON data")
            
            for script in script_tags:
                try:
                    script_json = json.loads(script.string)
                    if 'product' in script_json:
                        print(f"Found product data in script tag: {json.dumps(script_json['product'], indent=2)[:500]}...")
                        
                        if 'variants' in script_json['product']:
                            for variant in script_json['product']['variants']:
                                variant_info = {
                                    'id': variant.get('id'),
                                    'title': variant.get('title'),
                                    'price': variant.get('price'),
                                    'available': variant.get('available', True)
                                }
                                variants.append(variant_info)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Method 2: Look for variant options in select elements
        if not variants:
            print("Trying to find variants in select elements")
            variant_selects = soup.select('select[name="id"], select[id*="ProductSelect"]')
            for select in variant_selects:
                print(f"Found select element: {select.get('id', 'no-id')}")
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
                        print(f"Found variant: {variant_info}")
        
        # If no variants found, create a default variant with the product price
        if not variants:
            print("No variants found, trying to find variant ID in the page")
            # Try to find variant ID in the page
            variant_id_match = re.search(r'"id":(\d+),"available":true', response.text) or \
                              re.search(r'value="(\d+)"[^>]*>.*?</option>', response.text) or \
                              re.search(r'name="id"[^>]*value="(\d+)"', response.text)
                              
            if variant_id_match:
                variant_id = variant_id_match.group(1)
                print(f"Found variant ID: {variant_id}")
                variants.append({
                    'id': variant_id,
                    'title': 'Default',
                    'price': product_price,
                    'available': True
                })
        
        # Store product information
        product_info = {
            'title': product_title,
            'price': product_price,
            'url': url,
            'variants': variants,
            'domain': urlparse(url).netloc
        }
        
        # Print product information
        print(f"Product: {product_title}")
        print(f"Price: {product_price}")
        print(f"Found {len(variants)} variants")
        
        return product_info
        
    except Exception as e:
        print(f"Error fetching product info: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_product_fetch.py <product_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    product_info = fetch_product_info(url)
    
    if product_info:
        print("\nProduct Information:")
        print(json.dumps(product_info, indent=2))
    else:
        print("\nFailed to fetch product information")

if __name__ == "__main__":
    main()