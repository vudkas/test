# Shopify Card Checker Pro

A comprehensive tool for testing Shopify payment processing and checkout functionality.

## Features

- Card validation through Shopify payment gateways
- Proxy support with automatic rotation
- Telegram notifications for successful validations
- Export results to CSV
- Multi-threaded processing for faster validation
- Browser automation for sites with Cloudflare/hCaptcha protection

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

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
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

## Notes

- The klaritylifestyle.com site is protected by hCaptcha, which requires browser automation to solve.
- For complete checkout testing on protected sites, you may need to integrate a captcha solving service.