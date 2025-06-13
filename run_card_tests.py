#!/usr/bin/env python3
"""
Run multiple Shopify credit card tests with different proxies and cards
"""

import sys
import json
import time
import random
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('card_tests.log')
    ]
)
logger = logging.getLogger('run_card_tests')

# Test URLs
TEST_URLS = [
    "https://klaritylifestyle.com/products/power-stripe-skirt",
    "https://www.allbirds.com/products/mens-wool-runner-up-mizzles-natural-black",
    "https://www.gymshark.com/products/gymshark-arrival-5-shorts-black-ss21"
]

# Proxies
PROXIES = [
    "193.233.118.40:61234:user552:r7jugq38",
    "134.202.43.145:61234:user401:i5Jp8KCl",
    "46.232.76.52:61234:user564:ZRyvOBsB",
    "94.241.181.71:61234:user1095:7xfdKMGR",
    "88.135.111.38:61234:user2086:ST3SGDXU",
    "159.197.229.219:61234:user219:EniGCswd",
    "159.197.238.51:61234:user_7747e550dc7d:e1ULEKrY",
    "159.197.238.102:61234:user_4653065bc829:JqD6s22J",
    "159.197.238.119:61234:user_580cf90e5f40:Hc3rhpkH",
    "139.190.222.87:61234:user_282a376e0fb7:ftoYN3Pn"
]

# Credit cards
CREDIT_CARDS = [
    {"number": "5577557193296184", "month": "05", "year": "2026", "cvv": "620"},
    {"number": "5395937416657109", "month": "05", "year": "2026", "cvv": "364"},
    {"number": "4895040589255203", "month": "12", "year": "2027", "cvv": "410"},
    {"number": "5509890034510718", "month": "06", "year": "2028", "cvv": "788"}
]

def run_test(url, proxy, card):
    """
    Run a single test with the given URL, proxy, and card
    
    Args:
        url: URL of the product page
        proxy: Proxy string
        card: Dictionary with card details
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Running test for {url}")
    logger.info(f"Using proxy: {proxy}")
    logger.info(f"Using card: {card['number']}")
    
    # Build the command
    cmd = [
        "python3", "shopify_card_tester.py",
        "--url", url,
        "--proxy", proxy,
        "--cc", card["number"],
        "--month", card["month"],
        "--year", card["year"],
        "--cvv", card["cvv"]
    ]
    
    # Run the command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Parse the output
        if result.returncode == 0:
            try:
                output = result.stdout.strip()
                json_start = output.rfind('{')
                if json_start >= 0:
                    json_str = output[json_start:]
                    test_result = json.loads(json_str)
                    
                    # Add metadata
                    test_result["url"] = url
                    test_result["proxy"] = proxy
                    test_result["card"] = card["number"]
                    test_result["timestamp"] = datetime.now().isoformat()
                    
                    return test_result
                else:
                    logger.error(f"No JSON output found: {output}")
                    return {
                        "success": False,
                        "error": "No JSON output found",
                        "url": url,
                        "proxy": proxy,
                        "card": card["number"],
                        "timestamp": datetime.now().isoformat()
                    }
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON output: {e}")
                return {
                    "success": False,
                    "error": f"Error parsing JSON output: {str(e)}",
                    "url": url,
                    "proxy": proxy,
                    "card": card["number"],
                    "timestamp": datetime.now().isoformat()
                }
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return {
                "success": False,
                "error": f"Command failed with return code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "url": url,
                "proxy": proxy,
                "card": card["number"],
                "timestamp": datetime.now().isoformat()
            }
    except subprocess.TimeoutExpired:
        logger.error("Command timed out after 5 minutes")
        return {
            "success": False,
            "error": "Command timed out after 5 minutes",
            "url": url,
            "proxy": proxy,
            "card": card["number"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return {
            "success": False,
            "error": f"Error running command: {str(e)}",
            "url": url,
            "proxy": proxy,
            "card": card["number"],
            "timestamp": datetime.now().isoformat()
        }

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run multiple Shopify credit card tests')
    parser.add_argument('--url', help='Specific URL to test')
    parser.add_argument('--proxy', help='Specific proxy to use')
    parser.add_argument('--card', type=int, choices=[0, 1, 2, 3], help='Specific card index to use (0-3)')
    parser.add_argument('--max-tests', type=int, default=3, help='Maximum number of tests to run')
    args = parser.parse_args()
    
    # Determine which URLs to test
    urls_to_test = [args.url] if args.url else TEST_URLS
    
    # Determine which proxies to use
    proxies_to_use = [args.proxy] if args.proxy else PROXIES
    
    # Determine which cards to use
    cards_to_use = [CREDIT_CARDS[args.card]] if args.card is not None else CREDIT_CARDS
    
    # Run the tests
    results = []
    test_count = 0
    
    for url in urls_to_test:
        # Shuffle proxies and cards for randomness
        random.shuffle(proxies_to_use)
        random.shuffle(cards_to_use)
        
        # Use a different proxy and card for each URL
        proxy = proxies_to_use[0]
        card = cards_to_use[0]
        
        # Run the test
        result = run_test(url, proxy, card)
        results.append(result)
        test_count += 1
        
        # Check if we've reached the maximum number of tests
        if test_count >= args.max_tests:
            break
            
        # Wait between tests to avoid rate limiting
        time.sleep(10)
    
    # Save results to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"card_test_results_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {filename}")
    
    # Print summary
    success_count = sum(1 for r in results if r.get("success", False))
    failure_count = len(results) - success_count
    
    logger.info(f"Tests completed: {len(results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failure_count}")
    
    if success_count > 0:
        logger.info("Successful tests:")
        for r in results:
            if r.get("success", False):
                logger.info(f"- {r['url']} with card {r['card']}")


if __name__ == "__main__":
    main()