# Payment Gateway Test Results

## Test Environment
- Website: shopjustthething.com
- Product: Stripe Poppy Smocked Top
- Checkout URL: https://shopjustthething.com/checkouts/cn/Z2NwLXVzLWNlbnRyYWwxOjAxSldYOFdRN0RIQlI1R1c0NTBWQ0IwOEdW/

## Payment Gateway
- Identified Gateway: Stripe

## Test Cards and Results

### Card 1
- Card Number: 5406685147354036
- Expiration: 04/32
- CVV: 530
- Result: Declined
- Error Message: "Your card was declined. Try again or use a different payment method."

### Card 2
- Card Number: 4031630131694605
- Expiration: 06/29
- CVV: 091
- Result: Declined
- Error Message: "Your card was declined. Try again or use a different payment method."

## Additional Notes
- Both test cards produced the same decline message
- No 3D Secure authentication was triggered for either card
- Shipping and billing addresses were set to the same address
- Total order amount: $185.20 USD