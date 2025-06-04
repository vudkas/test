# Shopify Card Checker Pro

A comprehensive tool for testing Shopify payment processing and checkout functionality.

## Features

- Card validation through Shopify payment gateways
- Proxy support with automatic rotation
- Telegram notifications for successful validations
- Export results to CSV
- Multi-threaded processing for faster validation
- Browser automation for sites with Cloudflare/hCaptcha protection
- Detailed payment result analysis with charge amount detection
- Support for multiple payment gateways and error types

## Components

### 1. Card Checker Web Interface

The main application provides a web interface for validating credit cards through Shopify payment gateways.

- **app.py**: Flask web server that provides the API endpoints
- **main.py**: Core payment processing logic
- **templates/index.html**: Web interface for the card checker

### 2. Checkout Testing Scripts

Two scripts are provided for testing the checkout process:

- **test_checkout.py**: Simple requests-based checkout testing (works for sites without protection)
- **browser_checkout.py**: Browser-based checkout testing (works for sites with Cloudflare/hCaptcha)
- **card_tester.py**: Automated testing of multiple cards on multiple sites

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
pip install selenium  # For browser automation
```

2. For browser automation, install Chrome and ChromeDriver:
```
# Install Chrome
apt-get update && apt-get install -y wget gnupg2
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update && apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}.0.7151.68/linux64/chromedriver-linux64.zip"
unzip /tmp/chromedriver.zip -d /tmp
mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
```

## Usage

### Running the Card Checker Web Interface

```
python app.py
```

This will start the web server on port 12000. Access the interface at http://localhost:12000.

### Testing Checkout Process

For sites without protection:
```
python test_checkout.py [URL]
```

For sites with Cloudflare/hCaptcha protection:
```
python browser_checkout.py [URL]
```

To test with a credit card:
```
python browser_checkout.py [URL] [CC] [MONTH] [YEAR] [CVV]
```

## Workflow

1. User enters a Shopify product URL and validates it
2. User configures proxy settings (optional)
3. User enters credit card information to test
4. The system:
   - Validates the product URL and extracts product information
   - Adds the product to cart
   - Extracts cart session and cookies
   - Proceeds to checkout
   - Gets the checkout URL and location path
   - Sets shipping and billing address with email raven.usu@gmail.com
   - Processes the payment with the provided card
   - Returns detailed results including:
     - Success/failure status
     - Payment gateway used
     - Charge amount (if successful)
     - Detailed error message (if failed)
     - 3D Secure or redirect status (if applicable)

## Enhanced Features

- **Improved Error Detection**: Better detection of CVV errors, AVS errors, and insufficient funds errors
- **Charge Amount Detection**: Extracts and displays the charge amount for successful transactions
- **Email Configuration**: Uses raven.usu@gmail.com for all checkout processes
- **Session Extraction**: Extracts and returns cart session, checkout token, and location path
- **Multiple Payment Endpoints**: Tries multiple Shopify payment endpoints for better compatibility
- **Enhanced Gateway Detection**: Improved detection of payment gateway types

## Notes

- The system now handles various payment responses including:
  - Successful charges with amount detection
  - CVV verification failures (card is valid)
  - AVS verification failures (card is valid)
  - Insufficient funds errors (card is valid)
  - 3D Secure redirects
  - External payment processor redirects
  - Declined transactions

## Current Status

- All enhancements have been implemented and tested
- Email is now set to raven.usu@gmail.com throughout the application
- Improved error handling and detection for various payment scenarios
- Enhanced extraction of checkout information and payment results

### Known Issues

- Some Shopify stores may have additional protection that requires captcha solving
- For sites with advanced protection, consider using a dedicated proxy service
- 3D Secure verification requires manual intervention and cannot be fully automated