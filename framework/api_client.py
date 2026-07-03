"""
Reusable HTTP client for the API test framework.

Wraps `requests` with:
  - a configurable base URL per API
  - automatic retry with backoff on network-level failures
  - structured logging of every request/response
  - a single point to plug in auth headers, timeouts, etc.
"""
import time
from typing import Any, Dict, Optional

import requests

from framework.logger import get_logger

logger = get_logger()


class APIError(Exception):
    """Raised when a request fails after all retry attempts are exhausted."""


class APIClient:
    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        max_retries: int = 2,
        retry_backoff: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def _full_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.base_url}{endpoint}"

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url = self._full_url(endpoint)
        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt <= self.max_retries:
            try:
                logger.info(f"--> {method.upper()} {url} | params={params} | body={json_body}")
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                    timeout=self.timeout,
                )
                logger.info(f"<-- {response.status_code} {url} | body={response.text[:500]}")
                return response
            except requests.exceptions.RequestException as exc:
                last_exc = exc
                attempt += 1
                logger.warning(f"Request error on attempt {attempt}/{self.max_retries + 1}: {exc}")
                if attempt <= self.max_retries:
                    time.sleep(self.retry_backoff * attempt)

        raise APIError(f"Request to {url} failed after {self.max_retries + 1} attempts: {last_exc}")

    # Convenience wrappers -------------------------------------------------
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)
