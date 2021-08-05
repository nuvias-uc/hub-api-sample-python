# Hub API Sample - Python

This script demonstrates the Hub API. For more information please visit
<https://developer.nuvias-uc.com>.

The script shows the following steps:
1. Successful authentication with the API.
1. Retrieval of some useful data.
1. Creation of one basket

In reality Hub API users will rarely create baskets but instead will create
orders directly. The API for this is very similar to that of creating a basket.

**IMPORTANT**: Do not create test orders without first speaking with Nuvias UC,
otherwise your orders will be shipped at your cost.

Access to the Hub API requires an existing reseller relationship with Nuvias UC.

This script is provided purely for example purposes and should not be used
as-is by any customer.

## Running the script

The script requires the following environment variables, which can be easily
provided by creating a `.env` file:

| Name | Meaning |
| --- | --- |
| CLIENT_ID | The Hub API client ID |
| CLIENT_SECRET | The Hub API client secret |

You can create both of these from the *API Clients* tab in Hub.

Execute the script as follows:

```
% pipenv run hub-api-sample
Loading .env environment variables...
Successfully authenticated as Ian Loncotel
Successfully created basket 3026
https://hub.staging.nuvias-uc.com/webstore/baskets/3026/
```

You can visit the URL provided to view the basket that you have just created.