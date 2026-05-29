tastytrade API Intro
New users should start by following the steps below. They will walk you through some of the key features of the tastytrade API such as logging in, submitting an order, viewing your positions, and closing a position.

For an overview of API rules and patterns, you can head to the API Overview page.

For an overview of some core tastytrade concepts, head to the High-level Concepts section of our API Overview.

If you just want to see the docs, head to the API Docs page.

Environments
We have 2 environments you can use: Sandbox and Production. Each environment is separate, meaning you will have different credentials for each.

Sandbox - a test environment where everything is fake and you can test your applications before putting real money to use. Head to the Sandbox page for more information about this environment.
URL: https://api.cert.tastyworks.com
Production - our live environment where everything is real and trades do matter. You can start using this environment when you feel ready. We recommend testing your code in the sandbox environment before hitting the production environment.
URL: https://api.tastyworks.com
Getting Started
1. Create a Sandbox Account
You should start by creating an account in our sandbox environment using the Sandbox page. We have a whole working test environment that you will be able to build your application and test in prior to hooking up your production account.

2. Generate an Oauth2 access token
Every request you make needs an Authorization header with a valid access token.

Head to our Auth Patterns Overview more info about sessions and the Authorization header.

3. Submit a Trade
Submit a trade by hitting our Submit Order endpoint.

You can find detailed instructions about how to structure an order on our Order Submission page.

Our Sandbox environment has custom logic around order submission that makes it easy to simulate an order fill, partial fill, or a live order. Head to our Sandbox Page for more info.

4. Fetch Your Account Balance and Positions
Once your order fills, a new position will be created in your account. Your account balance will also be updated to reflect the cost of the order.

Hit our List Account Positions endpoint to fetch your account positions.

Hit our List Account Balances endpoint to view your account balance.

5. Stream Market Data
Our Streaming Market Data page has all the info you need to fetch quotes. The quotes will be delayed in our Sandbox environment. Production environment quotes are real-time.

6. Fetch Market Data
You can also fetch a quote via http. Our Market Data Guide will get you started.

7. Stream Account Updates
To get real time updates regarding your account, head to our Streaming Account Data page.

8. Close a Position
Closing a position is done by submitting an order in the opposite direction as the position. For example, if you are long 100 shares of AAPL, you can submit a Sell to Close order for 100 shares of AAPL. When this order fills, your position will be zeroed out.

For more information on closing and opening, head to our Leg Attributes section of the Order Submission page.

9. Fetch an Option Chain
If you want to see a full option chain for a ticker symbol, head to our List Nested Option Chains section. This will list every put and call symbol for every expiration that tastytrade supports for the given ticker symbol. It also includes the streamer-symbol, which is the symbol to use when subscribing to quote data from DxLink.

Running into issues or have questions?
Head to our FAQ page to see if your question can be answered there.

We also have a dedicated Service Desk ready to assist you. Please submit an email to api.support@tastytrade.com in order to create a ticket, and a member of our team will be in touch.

