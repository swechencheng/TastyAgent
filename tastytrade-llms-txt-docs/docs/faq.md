Frequently Asked Questions
Why am I suddenly getting unconfirmed_user errors?
All users must confirm their email address within 3 days of signing up. This includes sandbox users.

To confirm your email address, you must request a confirmation email:

curl -X POST https://api.cert.tastyworks.com/confirmation -H "Content-Type: application/json" -d '{ "email": "<insert your user email here>" }'
Check your inbox for a link to confirm your email address. Once you've clicked the link and see a success message, you are good to go.

Why do I keep getting invalid_credentials errors?
This error occurs when you are entering your username/password wrong during login. Be sure that you are hitting the correct environment. We have a sandbox environment and a production environment. Each environment requires you to have a separate set of credentials (username and password). If you hit the production environment with your sandbox credentials, you'll likely see this invalid_credentials error.

To diagnose which environment you are hitting, check the url of your request. The sandbox environment's base URL is https://api.cert.tastyworks.com. The production environment's base URL is different: https://api.tastyworks.com. Check

If needed, you can reset your production password at tastytrade.com.

Why am I getting a 401 when my credentials are valid?
tastytrade has specific requirements around the User-Agent header. The format should be <product>/<version>, otherwise you'll get a 401 with a response like this:

<html>

<head>
  <title>401 Authorization Required</title>
</head>

<body>
  <center>
    <h1>401 Authorization Required</h1>
  </center>
  <hr>
  <center>nginx</center>
</body>

</html>
Head to our API Conventions section for more info.

Why are my http requests suddenly timing out?
tastytrade will block your IP address outright if we receive too many failed login attempts within a short period of time. We do this to protect our users' accounts from being brute forced.

The IP address block typically lasts 8 hours. During that time, you won't be able to connect to any of our endpoints. Instead, your request will time out.

You can contact api.support@tastytrade.com to ask to be unblocked.

How do I reset my sandbox user password?
Head to the Sandbox page and look for the "Reset it here" link under the sign in button. Enter your email address in the provided field and check your inbox for further instructions.

Can I delete my sandbox user?
No, you cannot delete your sandbox user. If you no longer have access to the email account, please contact api.support@tastytrade.com.

Why am I getting unauthorized errors?
This error occurs when you don't have a valid access token. Access tokens last 15 minutes and must be sent with every request in the Authorization header. See our Auth Patterns section for more info. You need to generate an access token and include the access token as the value of the Authorization header in every subsequent request.

I can't access your sandbox environment
If you see errors like Failed to resolve or ENOTFOUND, be sure you are using the correct URL. Our sandbox environment's URL is api.cert.tastyworks.com. To fetch your accounts, you would need to hit api.cert.tastyworks.com/customers/me/accounts, for example.

I am having trouble getting quotes
Head to our Streaming Market Data section for instructions on how to stream quotes. It is a multi-step process, starting with fetching an api quote token from tastytrade and using that token to authenticate with our quote provider - DxLink.

Do you have any sample code I can use to get started?
Head to the SDKs page to see if we offer anything in your preferred language.

We also have a public Postman workspace that anyone can use to start sending api requests to our sandbox environment. You can find it here.