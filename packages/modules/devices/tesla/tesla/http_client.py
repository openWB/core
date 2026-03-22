import logging
import time
import threading

import requests
from requests.exceptions import (
    ConnectionError,
    RequestException,
    SSLError,
    Timeout,
)

log = logging.getLogger(__name__)


class PowerwallHttpClient:
    """
    HTTP client wrapper for Tesla Powerwall Gateway local API calls.

    Logging goals:
    - Show whether calls are executed from a single thread or multiple threads
    - Clearly distinguish:
        * transport errors (timeouts, connection refused, no route, TLS)
        * HTTP errors (401/403/5xx)
        * JSON parse errors (HTML/text instead of JSON)
    """

    def __init__(self, host: str, session: requests.Session, cookies):
        self.__base_url = "https://" + host
        self.__host = host
        self.cookies = cookies
        self.__session = session
        self.cycle_failed = False  # fail-fast flag, reset each polling cycle

    def reset_cycle(self):
        """Reset per-update-cycle fail-fast flag."""
        self.cycle_failed = False

        self.cookie_renewed = False  # set True when new auth cookie negotiated
    def mark_cookie_renewed(self):
        """Mark that a new auth cookie was negotiated in this update cycle."""
        self.cookie_renewed = True

    def get_json(self, relative_url: str, fail_fast: bool = True):
        url = self.__base_url + relative_url
        t0 = time.monotonic()
        thread_name = threading.current_thread().name
        thread_id = threading.get_ident()

        # --- transport / network errors (no HTTP response at all)
        try:
            resp = self.__session.get(
                url,
                cookies=self.cookies,
                verify=False,
                timeout=5
            )
        except (Timeout, ConnectionError, SSLError) as e:
            dt_ms = int((time.monotonic() - t0) * 1000)
            log.warning(
                "Powerwall TRANSPORT error host=%s path=%s thread=%s(%s) dt_ms=%s err=%s",
                self.__host,
                relative_url,
                thread_name,
                thread_id,
                dt_ms,
                repr(e),
            )
            if fail_fast:
                self.cycle_failed = True
            raise
        except RequestException as e:
            dt_ms = int((time.monotonic() - t0) * 1000)
            log.warning(
                "Powerwall REQUEST exception host=%s path=%s thread=%s(%s) dt_ms=%s err=%s",
                self.__host,
                relative_url,
                thread_name,
                thread_id,
                dt_ms,
                repr(e),
            )
            if fail_fast:
                self.cycle_failed = True
            raise

        dt_ms = int((time.monotonic() - t0) * 1000)
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        clen = resp.headers.get("Content-Length")

        # --- HTTP-level errors (we did get a response)
        if resp.status_code >= 400:
            log.warning(
                "Powerwall HTTP error host=%s path=%s status=%s thread=%s(%s) "
                "dt_ms=%s ctype=%s clen=%s",
                self.__host,
                relative_url,
                resp.status_code,
                thread_name,
                thread_id,
                dt_ms,
                ctype,
                clen,
            )
            if fail_fast:
                self.cycle_failed = True
            resp.raise_for_status()

        # --- JSON parsing
        try:
            return resp.json()
        except ValueError as e:
            preview = ""
            try:
                preview = (resp.text or "")[:200].replace("\n", "\\n").replace("\r", "\\r")
            except Exception:
                preview = "<unavailable>"

            log.warning(
                "Powerwall JSON parse error host=%s path=%s status=%s thread=%s(%s) "
                "dt_ms=%s ctype=%s preview=%s",
                self.__host,
                relative_url,
                resp.status_code,
                thread_name,
                thread_id,
                dt_ms,
                ctype,
                preview,
            )
            if fail_fast:
                self.cycle_failed = True
            raise

