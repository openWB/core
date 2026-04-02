import logging

import requests
from requests.exceptions import HTTPError, ConnectionError, RequestException, SSLError, Timeout

log = logging.getLogger(__name__)


class PowerwallHttpClient:
    """
    HTTP client wrapper for Tesla Powerwall Gateway local API calls.
    """

    def __init__(self, host: str, session: requests.Session, cookies):
        self.__base_url = "https://" + host
        self.cookies = cookies
        self.__session = session

        # Fail-fast marker for the current polling cycle
        self.cycle_failed = False

        # Marker: set when a new auth cookie was negotiated (startup or reauth)
        self.cookie_renewed = False

    def reset_cycle(self):
        """Reset per update-cycle flags."""
        self.cycle_failed = False
        self.cookie_renewed = False

    def mark_cookie_renewed(self):
        """Mark that cookies have been freshly negotiated (start or reauth)."""
        self.cookie_renewed = True

    def get_json(self, relative_url: str, *, fail_fast: bool = True):
        """
        :param fail_fast:
            True  -> errors mark this cycle as failed (device aborts remaining components)
            False -> errors do NOT mark cycle_failed (for non-critical endpoints like /api/status)
        """
        url = self.__base_url + relative_url

        try:
            response = self.__session.get(
                url,
                cookies=self.cookies,
                verify=False,
                timeout=5,
            )
            return response.json()
        except (HTTPError, Timeout, ConnectionError, SSLError, RequestException, ValueError):
            if fail_fast:
                self.cycle_failed = True
            raise