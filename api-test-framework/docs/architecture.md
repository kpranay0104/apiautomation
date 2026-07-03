# Framework Architecture

```
api-test-framework/
├── .github/workflows/api-tests.yml   # CI pipeline (GitHub only reads workflows from this path)
├── conftest.py                       # discovers tests/test_reqres.yaml, resolves base_url,
│                                      # parametrizes pytest
├── tests/
│   ├── test_api.py                   # single generic test function that executes every case
│   └── test_reqres.yaml              # the test cases themselves (data, not code)
├── framework/
│   ├── api_client.py                 # requests wrapper: retries, timeouts, logging
│   ├── test_loader.py                # YAML -> list[dict] test case loader
│   ├── utils.py                      # env var resolution, dot-notation dict, safe assertion eval
│   └── logger.py                     # console + file logging setup
├── docs/                             # this folder
├── requirements.txt
├── pytest.ini
└── reports/                          # HTML/JUnit output (git-ignored, produced at run time)
```

## How a test case becomes a pytest test

1. `conftest.py` implements `pytest_generate_tests`, which globs
   `tests/*.yaml` files and loads them via `framework/test_loader.py`.
2. Each dict in the resulting list becomes one parametrized instance of the
   `test_case` fixture, with a readable id like
   `test_reqres.yaml::Get single user`.
3. `tests/test_api.py::test_api_case` receives one `test_case` dict per run
   (plus the resolved `base_url` fixture), builds/reuses an `APIClient`,
   fires the request, checks `expected_status`, then evaluates each string
   in `assertions` against the parsed response body.

This means **adding a test case never requires writing a new Python
function** — only YAML.

## How the base URL is resolved

`conftest.py` defines a session-scoped `base_url` fixture, checked in this
order:

1. `--base-url` command-line flag
2. `BASE_URL` in `.env` (loaded automatically via `python-dotenv`) or the
   shell environment
3. `DEFAULT_BASE_URL` constant (`https://reqres.in`)

`tests/test_api.py` requests this fixture and passes it into `APIClient`, so
no code changes are needed to point the whole suite at a different host.

## Design choices

- **Data-driven, not code-driven** — test authors who don't write Python can
  still add coverage by editing YAML.
- **Safe assertion DSL** — assertion strings are parsed with `ast` and
  checked against an allow-list before `eval`, so a typo can't accidentally
  execute arbitrary code, and reviewers can trust what a `.yaml` file can do.
- **Retry + logging built into the client** — flaky network conditions
  (common with free public APIs) don't cause spurious CI failures, and every
  request/response pair is logged to `reports/test_run.log` for debugging.
- **Configurable base URL** — no hardcoded host, so the same suite can run
  against production, staging, or a local mock server just by changing a
  flag or `.env` value.
