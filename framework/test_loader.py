"""
Loads structured test case definitions from .yaml/.yml/.json files.

Expected file format (a top-level "tests" list, or a bare list):

    tests:
      - name: Get user details
        base_url: reqres
        method: GET
        endpoint: /api/users/2
        expected_status: 200
        assertions:
          - response.data.id == 2
"""
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

REQUIRED_FIELDS = ("name", "method", "endpoint")


class TestCaseFormatError(ValueError):
    pass


def load_test_cases(filepath: str) -> List[Dict[str, Any]]:
    path = Path(filepath)

    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        elif path.suffix == ".json":
            data = json.load(f)
        else:
            raise TestCaseFormatError(f"Unsupported test file type: {filepath}")

    if isinstance(data, dict) and "tests" in data:
        cases = data["tests"]
    elif isinstance(data, list):
        cases = data
    else:
        raise TestCaseFormatError(
            f"{filepath}: expected a top-level 'tests' list or a bare list of test cases"
        )

    for case in cases:
        missing = [field for field in REQUIRED_FIELDS if field not in case]
        if missing:
            raise TestCaseFormatError(
                f"{filepath}: test case {case.get('name', '<unnamed>')} missing required field(s): {missing}"
            )

    return cases
