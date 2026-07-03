"""
Executes every test case discovered by conftest.py's pytest_generate_tests.

Each YAML test case is turned into one pytest test (visible individually in
`-v` output and in the HTML/JUnit reports) that:
  1. Sends the HTTP request via the reusable APIClient, against `base_url`
     (resolved by conftest.py from --base-url / .env / a default)
  2. Asserts the expected status code (if given)
  3. Evaluates each assertion expression against the parsed response body
"""
import pytest

from framework.api_client import APIClient, APIError
from framework.logger import get_logger
from framework.utils import evaluate_assertion, resolve_env_vars

logger = get_logger()

_clients = {}


def _client_for(url: str, api_key: str) -> APIClient:
    if url not in _clients:
        _clients[url] = APIClient(url, default_headers={"x-api-key": api_key})
    return _clients[url]


def test_api_case(test_case, base_url, api_key):
    name = test_case["name"]
    method = test_case["method"]
    endpoint = test_case["endpoint"]
    payload = resolve_env_vars(test_case.get("payload"))
    params = resolve_env_vars(test_case.get("params"))
    headers = resolve_env_vars(test_case.get("headers"))
    expected_status = test_case.get("expected_status")
    assertions = test_case.get("assertions", [])

    client = _client_for(base_url, api_key)

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
