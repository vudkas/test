# Payment Gateway Test Results

## Test Environment 1
- Website: shopjustthething.com
- Product: Stripe Poppy Smocked Top
- Checkout URL: https://shopjustthething.com/checkouts/cn/Z2NwLXVzLWNlbnRyYWwxOjAxSldYOFdRN0RIQlI1R1c0NTBWQ0IwOEdW/

### Payment Gateway
- Identified Gateway: Stripe

### Test Cards and Results

#### Card 1
- Card Number: 5406685147354036
- Expiration: 04/32
- CVV: 530
- Result: Declined
- Error Message: "Your card was declined. Try again or use a different payment method."

#### Card 2
- Card Number: 4031630131694605
- Expiration: 06/29
- CVV: 091
- Result: Declined
- Error Message: "Your card was declined. Try again or use a different payment method."

### Additional Notes
- Both test cards produced the same decline message
- No 3D Secure authentication was triggered for either card
- Shipping and billing addresses were set to the same address
- Total order amount: $185.20 USD

## Test Environment 2
- Website: eraofpeace.org
- Product: Donation
- Checkout URL: https://eraofpeace.org/checkouts/cn/Z2NwLXVzLWNlbnRyYWwxOjAxSldYQlo5TUZDUE03S0JaWTdSNTExR01G

### Payment Gateway
- Identified Gateway: Shopify Payments

### Test Cards and Results

#### Card 1
- Card Number: 4213630013499628
- Expiration: 09/28
- CVV: 988
- Result: Declined
- Error Message: "Your card was declined."

#### Card 2
- Card Number: 5356810054178190
- Expiration: 06/27
- CVV: 572
- Result: Declined
- Error Message: "Your card was declined."

#### Card 3
- Card Number: 4622391115565643
- Expiration: 11/27
- CVV: 108
- Result: Declined
- Error Message: "Your card was declined."

#### Card 4
- Card Number: 5509890032421892
- Expiration: 11/27
- CVV: 017
- Result: Declined
- Error Message: "Your card was declined."

#### Card 5
- Card Number: 5455122807222246
- Expiration: 06/28
- CVV: 999
- Result: Declined
- Error Message: "Your card was declined."

#### Card 6
- Card Number: 4632252055500305
- Expiration: 12/28
- CVV: 730
- Result: Declined
- Error Message: "Your card was declined."

#### Card 7
- Card Number: 5169201653090928
- Expiration: 03/29
- CVV: 562
- Result: Declined
- Error Message: "Your card was declined."

#### Card 8
- Card Number: 4411037149484856
- Expiration: 05/29
- CVV: 259
- Result: Declined
- Error Message: "Your card was declined."

#### Card 9
- Card Number: 379186167572585
- Expiration: 06/25
- CVV: 2778
- Result: Declined
- Error Message: "Your card was declined."

### Additional Notes
- All test cards produced the same decline message
- No 3D Secure authentication was triggered for any card
- Shipping and billing addresses were set to the same address
- Total order amount: $1.00 USD

## Test Environment 3
- Website: store.zionpark.org
- Product: Donation
- Checkout URL: https://store.zionpark.org/checkouts/

### Payment Gateway
- Identified Gateway: Shopify Payments

### Test Cards and Results

#### Card 1
- Card Number: 4213630013499628
- Expiration: 09/28
- CVV: 988
- Result: Declined
- Error Message: "Your card was declined."

#### Card 2
- Card Number: 5356810054178190
- Expiration: 06/27
- CVV: 572
- Result: Declined
- Error Message: "Your card was declined."

#### Card 3
- Card Number: 4622391115565643
- Expiration: 11/27
- CVV: 108
- Result: Declined
- Error Message: "Your card was declined."

#### Card 4
- Card Number: 5509890032421892
- Expiration: 11/27
- CVV: 017
- Result: Declined
- Error Message: "Your card was declined."

#### Card 5
- Card Number: 5455122807222246
- Expiration: 06/28
- CVV: 999
- Result: Declined
- Error Message: "Your card was declined."

#### Card 6
- Card Number: 4632252055500305
- Expiration: 12/28
- CVV: 730
- Result: Declined
- Error Message: "Your card was declined."

#### Card 7
- Card Number: 5169201653090928
- Expiration: 03/29
- CVV: 562
- Result: Declined
- Error Message: "Your card was declined."

#### Card 8
- Card Number: 4411037149484856
- Expiration: 05/29
- CVV: 259
- Result: Declined
- Error Message: "Your card was declined."

#### Card 9
- Card Number: 379186167572585
- Expiration: 06/25
- CVV: 2778
- Result: Declined
- Error Message: "Your card was declined."

### Additional Notes
- All test cards produced the same decline message
- No 3D Secure authentication was triggered for any card
- Shipping and billing addresses were set to the same address
- Total order amount: $1.00 USD

## Summary of Findings
- None of the test cards were successfully processed on any of the three sites
- All sites returned a generic "Your card was declined" error message
- No "thank_you" URL was observed in any of the checkout flows, indicating all payments were declined
- The payment gateway appears to be Stripe on shopjustthething.com and Shopify Payments on the other two sites