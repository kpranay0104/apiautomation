"""
Executes every test case discovered by conftest.py's pytest_generate_tests.

Each YAML/JSON test case is turned into one pytest test (visible individually
in `-v` output and in the HTML/JUnit reports) that:
  1. Sends the HTTP request via the reusable APIClient
  2. Asserts the expected status code (if given)
  3. Evaluates each assertion expression against the parsed response body
"""
import os

import pytest

from framework.api_client import APIClient, APIError
from framework.logger import get_logger
from framework.utils import evaluate_assertion, resolve_env_vars

logger = get_logger()

BASE_URLS = {
    "reqres": "https://reqres.in",
    "jsonplaceholder": "https://jsonplaceholder.typicode.com",
    "openweather": "https://api.openweathermap.org",
}

_clients = {}


def _client_for(base_url_key: str) -> APIClient:
    if base_url_key not in BASE_URLS:
        raise ValueError(f"Unknown base_url key '{base_url_key}'. Known: {list(BASE_URLS)}")
    if base_url_key not in _clients:
        _clients[base_url_key] = APIClient(BASE_URLS[base_url_key])
    return _clients[base_url_key]


def test_api_case(test_case):
    name = test_case["name"]
    base_url_key = test_case.get("base_url", "jsonplaceholder")
    method = test_case["method"]
    endpoint = test_case["endpoint"]
    payload = resolve_env_vars(test_case.get("payload"))
    params = resolve_env_vars(test_case.get("params"))
    headers = resolve_env_vars(test_case.get("headers"))
    expected_status = test_case.get("expected_status")
    assertions = test_case.get("assertions", [])

    # Skip gracefully if a required secret (e.g. an API key) wasn't provided,
    # rather than failing the whole suite when run locally without secrets.
    if params:
        for key, value in params.items():
            if key == "appid" and not value:
                pytest.skip(f"{name}: OPENWEATHER_API_KEY not set in environment; skipping live call")

    client = _client_for(base_url_key)

    try:
        response = client.request(method, endpoint, params=params, json_body=payload, headers=headers)
    except APIError as exc:
        pytest.fail(f"[{name}] request failed: {exc}")

    if expected_status is not None:
        assert response.status_code == expected_status, (
            f"[{name}] expected status {expected_status}, got {response.status_code}. "
            f"Body: {response.text[:500]}"
        )

    try:
        body = response.json() if response.text else None
    except ValueError:
        body = None

    for assertion in assertions:
        try:
            result = evaluate_assertion(assertion, body, response.status_code)
        except Exception as exc:
            pytest.fail(f"[{name}] assertion errored: {assertion!r} -> {exc}")
        assert result, f"[{name}] assertion failed: {assertion!r} | response body: {body}"

    logger.info(f"PASSED: {name}")
