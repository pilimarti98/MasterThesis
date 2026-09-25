import logging
import requests
from typing import Any, Dict, Optional

# Configure basic logging to see troubleshooting logs in console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class APIClient:
    """A centralized client for interacting with the API at a specific base URL."""

    def __init__(self, base_url: str, timeout: int = 10, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Requests Session reuses TCP connections for better performance
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Central private method for all HTTP requests, logging, and error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logging.info(f"Sending {method.upper()} request to {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )

            # Logs HTTP status code for troubleshooting
            logging.info(f"Response Status: {response.status_code} [{url}]")

            # Automatically raises an HTTPError for 4xx or 5xx status codes
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err} | Response: {response.text}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            logging.error(f"Connection error occurred for {url}: {conn_err}")
            raise
        except requests.exceptions.Timeout:
            logging.error(f"Request timed out after {self.timeout}s: {url}")
            raise
        except requests.exceptions.RequestException as err:
            logging.error(f"An unexpected API error occurred: {err}")
            raise

    # -------------------------------------------------------------------------
    # Public Endpoint Methods
    # -------------------------------------------------------------------------

    def get_users(self) -> Dict[str, Any]:
        """Fetch users from /users endpoint."""
        return self._request("GET", "/users")

    def get_posts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch posts, optionally filtered by user ID."""
        params = {"userId": user_id} if user_id else None
        return self._request("GET", "/posts", params=params)