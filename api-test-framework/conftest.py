"""
Discovers every .yaml/.yml/.json test-case file under tests/ and parametrizes
the `test_case` fixture used by tests/test_api.py — this is what lets test
cases be authored as data (YAML) instead of as hand-written Python functions.
"""
import glob
import os

import pytest

from framework.test_loader import load_test_cases

TESTS_DIR = os.path.join(os.path.dirname(__file__), "tests")


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
