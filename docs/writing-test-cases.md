# Writing Test Cases

Test cases live in `tests/test_reqres.yaml` and are loaded automatically —
you never need to touch Python to add a new test.

## Schema

```yaml
tests:
  - name: <string, required>            # human-readable test name, shown in reports
    method: <string, required>          # GET | POST | PUT | PATCH | DELETE
    endpoint: <string, required>        # path appended to the base URL, e.g. /api/users/2
    params: <map, optional>             # query string parameters
    payload: <map, optional>            # JSON request body
    headers: <map, optional>            # extra request headers
    expected_status: <int, optional>    # asserted against response.status_code
    assertions: <list of strings, optional>
```

The base URL itself is *not* set per test case — it's resolved once per run
by `conftest.py` (command-line flag > `.env`/environment > default). See the
main [README](../README.md#configuring-the-base-url).

## Assertions

Each entry under `assertions` is a small Python-like boolean expression
evaluated against the parsed JSON response. Two variables are available:

- `response` — the parsed JSON body, with dot-notation access to nested fields
- `status_code` — the HTTP status code

Examples:

```yaml
assertions:
  - response.data.id == 2
  - response.data.email is not None
  - "'first_name' in response.data"
  - response.token is not None
  - status_code == 200
```

Only a safe subset of Python is allowed (comparisons, `in`, `len`, `str`,
`int`, `float`, `bool`, indexing, attribute access). Imports, lambdas, and
arbitrary function/method calls are rejected — see
`framework/utils.py::_validate_expression`.

## Secrets in test data

Use `${ENV_VAR_NAME}` anywhere in `params`, `payload`, or `headers` to pull a
value from the environment at run time (e.g. an API key you don't want
committed to the repo). Not needed for the Reqres tests today, but available
if you add an authenticated endpoint later.
