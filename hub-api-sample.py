from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from pydantic import BaseSettings
from requests_oauthlib import OAuth2Session
from urllib.parse import urljoin

import os
import sys


class Settings(BaseSettings):
    """Environment variables for configuration."""

    base_url: str = "https://hub.staging.nuvias-uc.com/"
    client_id: str
    client_secret: str


class HubAPIClient:
    """A demonstration client for a limited amount of the Hub API."""

    def __init__(self, base_url, client_id, client_secret):
        """
        Initialises a new HubAPIClient using the supplied API key.

        Args:
            base_url: The URL of Hub, without any path component.
                      E.g.: "https://hub.staging.nuvias-uc.com"
            client_id: The Hub API client ID
            client_secret: The Hub API client secret

        Raises:
            oauthlib.oauth2.rfc6749.errors.MissingTokenError: if the authentication is unsuccessful.
        """
        self._base_url = base_url
        token_url = urljoin(self._base_url, "/api/v1/oauth/create_token")
        client = BackendApplicationClient(client_id=client_id)
        oauth_body = client.prepare_request_body(
            client_secret=client_secret, include_client_id=True
        )
        self._session = OAuth2Session(client=client)
        self._session.fetch_token(token_url=token_url, body=oauth_body)

    def _get(self, path):
        """
        Retrieves a single GET endpoint from the Hub API, using the stored
        API credentials.

        Args:
            path: The complete path to the URL endpoint.
                  E.g.: "/api/v1/whoami"

        Returns:
            The API result converted back from JSON.
        """
        url = urljoin(self._base_url, path)
        return self._session.get(url).json()

    def _post(self, path, payload):
        """
        Triggers a single POST endpoint from the Hub API, using the stored
        API credentials.

        Args:
            path: The complete path to the URL endpoint.
                  E.g.: "/api/v1/whoami"
            payload: A python object representing the payload expected.

        Returns:
            The API result converted back from JSON.
        """
        url = urljoin(self._base_url, path)
        return self._session.post(url, json=payload).json()

    def whoami(self):
        """
        Determines information about the logged-in Hub user.

        Returns:
            A dictionary containing, amongst other things:
              id: The internal Hub user ID
              name: The user's full name
              organisation: The user's organisation ID
              currency: The user's currency ID
              local: The user's locale
              timezone: The user's timezone
        """
        return self._get("/api/v1/whoami")

    def get_country_id_by_iso_code(self, iso_code):
        """
        Determines the Hub country ID for the given ISO code.

        Args:
            iso_code: The 2-letter ISO 3166-1 code, e.g. "GB"

        Returns:
            The Hub ID (an int) or None if the country is not found.
        """

        countries = self._get("/api/v1/country_codes")

        for country in countries:
            if country["iso_code"] == iso_code:
                return country["id"]

        return None

    def get_shipping_types_for_country(self, country_id, name_filter=None):
        """
        Returns a list of shipping types that are valid for the given country ID.

        Params:
            country_id:
                The Hub country ID for the desired country.
            name_filter:
                Optional: Filter the returned list to return only those with this string
                somewhere in the name.

        Returns:
            A list of valid shipping types, which may be an empty list.
        """
        ship_types = self._get("/api/v1/shipping_types")
        valid_ship_types = []

        for ship_type in ship_types:
            if not ship_type["countries"]:
                # This type is good in any country
                valid_ship_types.append(ship_type)
                continue
            if ship_type["exclude_countries"]:
                # List contains countries where this type would be invalid
                if country_id not in ship_type["countries"]:
                    valid_ship_types.append(ship_type)
            else:
                # List contains countries where this type would be valid
                if country_id in ship_type["countries"]:
                    valid_ship_types.append(ship_type)

        if name_filter:
            filter_fn = lambda x: name_filter in x["name"]
            return list(filter(filter_fn, valid_ship_types))

        return valid_ship_types

    def create_basket(
        self,
        purchase_order_number,
        shipping_address,
        shipping_type,
        provisioning_instructions,
        line_items,
        name,
    ):
        """
        Creates a new basket.

        Params:
            purchase_order_number: Resellers PO number
            shipping_address: Customers delivery address
            shipping_type: ID of the desired shipping service
            provisioning_instructions: Instructions to go along with the provisioning SKU
            line_items: A list of items to be ordered
            name: A display name for this basket

        Returns:
            The basket created.
        """
        payload = {
            "purchase_order_number": purchase_order_number,
            "shipping_address": shipping_address,
            "shipping_type": shipping_type,
            "provisioning_instructions": provisioning_instructions,
            "line_items": line_items,
            "name": name,
        }
        return self._post("/api/v1/baskets", payload)


if __name__ == "__main__":
    settings = Settings()

    # Establish a connection to the Hub API
    try:
        client = HubAPIClient(
            settings.base_url, settings.client_id, settings.client_secret
        )
    except MissingTokenError:
        print("ERROR: Invalid Hub API credentials.", file=sys.stderr)
        sys.exit(-1)

    whoami = client.whoami()
    print("Successfully authenticated as {}".format(whoami["name"]))

    # Establish some parameters we'll need in order to place an order.
    # This logic is just an example - real users will need to add their
    # own logic here.
    gb = client.get_country_id_by_iso_code("GB")
    shipping_type = client.get_shipping_types_for_country(
        gb, name_filter="UK Standard"
    )[0]
    shipping_address = {
        "company_name": "Joe Bloggs Car Parts",
        "recipient_name": "Joe Bloggs",
        "addr_line_1": "2 Somewhere Street",
        "city": "Somewheretown",
        "postal_code": "SW1A 1AA",
        "country_code": gb,
    }
    line_items = [
        {
            "product_code": "2200-48820-025",
            "quantity": 3,
            "prov_product_code": "UD-SIP-SER-PRV-PH", 
        },
    ]

    # Create a basket
    basket = client.create_basket(
        purchase_order_number="TESTORDER0001",
        shipping_address=shipping_address,
        shipping_type=shipping_type["id"],
        provisioning_instructions="Use ResellerCom profile",
        line_items=line_items,
        name="API Sample Order",
    )
    print("Successfully created basket {}".format(basket["id"]))
    basket_url = urljoin(
        settings.base_url, "/webstore/baskets/{}/".format(basket["id"])
    )
    print(basket_url)
