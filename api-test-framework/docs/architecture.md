# Framework Architecture

```
api-test-framework/
├── .github/workflows/api-tests.yml   # active CI pipeline (GitHub only reads this path)
├── ci/github-actions.yml             # copy of the pipeline for reference/review
├── conftest.py                       # discovers *.yaml/*.json test files, parametrizes pytest
├── tests/
│   ├── test_api.py                   # single generic test function that executes every case
│   ├── test_reqres.yaml
│   ├── test_jsonplaceholder.yaml
│   └── test_openweathermap.yaml
├── framework/
│   ├── api_client.py                 # requests wrapper: retries, timeouts, logging
│   ├── test_loader.py                # YAML/JSON -> list[dict] test case loader
│   ├── utils.py                      # env var resolution, dot-notation dict, safe assertion eval
│   └── logger.py                     # console + file logging setup
├── docs/                             # this folder
├── requirements.txt
├── pytest.ini
└── reports/                          # HTML/JUnit output (git-ignored, produced at run time)
```

## How a test case becomes a pytest test

1. `conftest.py` implements `pytest_generate_tests`, which globs every
   `tests/*.yaml|*.yml|*.json` file and loads it via `framework/test_loader.py`.
2. Each dict in the resulting list becomes one parametrized instance of the
   `test_case` fixture, with a readable id like
   `test_reqres.yaml::Get single user`.
3. `tests/test_api.py::test_api_case` receives one `test_case` dict per run,
   builds/reuses an `APIClient` for the right base URL, fires the request,
   checks `expected_status`, then evaluates each string in `assertions`
   against the parsed response body.

This means **adding a test case never requires writing a new Python
function** — only YAML.

## Design choices

- **Data-driven, not code-driven** — test authors who don't write Python can
  still add coverage by editing YAML.
- **Safe assertion DSL** — assertion strings are parsed with `ast` and
  checked against an allow-list before `eval`, so a typo can't accidentally
  execute arbitrary code, and reviewers can trust what a `.yaml` file can do.
- **Retry + logging built into the client** — flaky network conditions
  (common with free public APIs) don't cause spurious CI failures, and every
  request/response pair is logged to `reports/test_run.log` for debugging.
- **Env-var templating (`${VAR}`)** — API keys stay out of the repo and are
  injected via GitHub Actions secrets in CI, or a local `.env` file.
