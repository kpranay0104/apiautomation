"""
Discovers every .yaml/.yml/.json test-case file under tests/ and parametrizes
the `test_case` fixture used by tests/test_api.py — this is what lets test
cases be authored as data (YAML) instead of as hand-written Python functions.

Also resolves two run-time settings, both --flag > .env/environment > default:
  - base_url: the API host to run tests against
  - api_key:  sent as the x-api-key header on every request (Reqres requires
              this on all endpoints — see https://reqres.in/signup for a free key)
"""
import glob
import os

import pytest
from dotenv import load_dotenv

from framework.test_loader import load_test_cases

load_dotenv()  # if a .env file exists in the repo root, its values are loaded
# into os.environ here — nothing happens if the file is absent.

TESTS_DIR = os.path.join(os.path.dirname(__file__), "tests")
DEFAULT_BASE_URL = "https://reqres.in"


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="API base URL to run tests against. Overrides BASE_URL from .env/environment.",
    )
    parser.addoption(
        "--api-key",
        action="store",
        default=None,
        help="Reqres x-api-key value. Overrides REQRES_API_KEY from .env/environment.",
    )


@pytest.fixture(scope="session")
def base_url(request):
    """Resolved once per test run: CLI flag > .env/environment > default."""
    return (
        request.config.getoption("--base-url")
        or os.environ.get("BASE_URL")
        or DEFAULT_BASE_URL
    )


@pytest.fixture(scope="session")
def api_key(request):
    """Resolved once per test run: CLI flag > .env/environment. No default —
    Reqres requires a real key; get a free one at https://reqres.in/signup."""
    key = request.config.getoption("--api-key") or os.environ.get("REQRES_API_KEY")
    if not key:
        pytest.exit(
            "No Reqres API key found. Set REQRES_API_KEY in .env, or pass --api-key. "
            "Get a free key at https://reqres.in/signup",
            returncode=1,
        )
    return key


def _discover_test_case_files():
    patterns = ("*.yaml", "*.yml", "*.json")
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(TESTS_DIR, pattern)))
    return sorted(files)


def pytest_generate_tests(metafunc):
    if "test_case" not in metafunc.fixturenames:
        return

    all_cases = []
    ids = []

    for filepath in _discover_test_case_files():
        source = os.path.basename(filepath)
        for case in load_test_cases(filepath):
            case = dict(case)
            case["_source_file"] = source
            all_cases.append(case)
            ids.append(f"{source}::{case['name']}")

    metafunc.parametrize("test_case", all_cases, ids=ids)
