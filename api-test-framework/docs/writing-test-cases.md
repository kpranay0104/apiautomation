# Writing Test Cases

Test cases live in `tests/*.yaml` (or `.json`) files and are loaded automatically
— you never need to touch Python to add a new API test.

## Schema

```yaml
tests:
  - name: <string, required>            # human-readable test name, shown in reports
    base_url: <string>                  # key from BASE_URLS in tests/test_api.py
                                         # (reqres | jsonplaceholder | openweather)
    method: <string, required>          # GET | POST | PUT | PATCH | DELETE
    endpoint: <string, required>        # path appended to base_url, e.g. /api/users/2
    params: <map, optional>             # query string parameters
    payload: <map, optional>            # JSON request body
    headers: <map, optional>            # extra request headers
    expected_status: <int, optional>    # asserted against response.status_code
    assertions: <list of strings, optional>
```

## Assertions

Each entry under `assertions` is a small Python-like boolean expression evaluated
against the parsed JSON response. Two variables are available:

- `response` — the parsed JSON body, with dot-notation access to nested fields
- `status_code` — the HTTP status code

Examples:

```yaml
assertions:
  - response.data.id == 2
  - response.data.email is not None
  - "'first_name' in response.data"
  - len(response) == 100
  - response[0].userId == 1
  - status_code == 200
```

Only a safe subset of Python is allowed (comparisons, `in`, `len`, `str`, `int`,
`float`, `bool`, indexing, attribute access). Imports, lambdas, and arbitrary
function/method calls are rejected — see `framework/utils.py::_validate_expression`.

## Secrets in test data

Use `${ENV_VAR_NAME}` anywhere in `params`, `payload`, or `headers` to pull a
value from the environment at run time (e.g. an API key that shouldn't be
committed to the repo):

```yaml
params:
  appid: ${OPENWEATHER_API_KEY}
```

If a required env var is missing, the framework resolves it to an empty
string; `tests/test_api.py` will skip that test case with a clear message
rather than failing the whole run.

## Adding a new API

1. Add its base URL to `BASE_URLS` in `tests/test_api.py`.
2. Create `tests/test_<api_name>.yaml` following the schema above.
3. Run `pytest` — new cases are picked up automatically, no other code changes needed.
