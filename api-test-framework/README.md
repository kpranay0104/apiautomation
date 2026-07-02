# API Test Automation Framework

A lightweight, reusable Python framework for testing REST APIs. Test cases are
authored as YAML data (no Python required to add coverage), executed with
`pytest` + `requests`, and wired into GitHub Actions for CI on every push/PR.

Demonstrated against three public APIs:

- [Reqres](https://reqres.in/) — users, login, create/update
- [JSONPlaceholder](https://jsonplaceholder.typicode.com/) — posts CRUD
- [OpenWeatherMap](https://openweathermap.org/api) — current weather lookup

## Repository layout

```
tests/       API test cases (YAML) + the generic pytest executor
framework/   Reusable client, loader, logger, assertion engine
ci/          Copy of the CI pipeline definition (see note below)
docs/        Test-case format & architecture docs
```

> **Note on `ci/`:** GitHub Actions only executes workflows placed under
> `.github/workflows/`, so the pipeline that actually runs lives there.
> `ci/github-actions.yml` is an identical copy kept for easy review alongside
> the other requirement folders — keep both in sync if you edit one.

## Local setup

```bash
git clone <your-repo-url>
cd api-test-framework
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

### API key for OpenWeatherMap

The weather tests need a free API key from https://openweathermap.org/api.

```bash
cp .env.example .env
# edit .env and set OPENWEATHER_API_KEY=...
export $(grep -v '^#' .env | xargs)   # or use your shell's preferred method
```

If the key isn't set, the two weather test cases are **skipped** (not
failed) with a clear message — every other test still runs.

## Running the tests

```bash
pytest
```

This runs every test case in `tests/*.yaml` and produces:

- Console output (`-v`, one line per test case)
- `reports/report.html` — self-contained HTML report
- `reports/junit.xml` — JUnit XML for CI integration
- `reports/test_run.log` — full request/response log for debugging

Run a single API's suite, or a single case, with normal pytest filters:

```bash
pytest -k "reqres"
pytest -k "Login successful"
```

## Adding a test case

No Python needed — add an entry to a file under `tests/`. See
[`docs/writing-test-cases.md`](docs/writing-test-cases.md) for the full
schema and assertion syntax. Example:

```yaml
tests:
  - name: Get user details
    base_url: reqres
    method: GET
    endpoint: /api/users/2
    expected_status: 200
    assertions:
      - response.data.id == 2
```

## Framework internals

See [`docs/architecture.md`](docs/architecture.md) for how test cases are
discovered and turned into pytest tests, and the design rationale behind the
retry logic, logging, and the safe assertion evaluator.

## CI/CD

`.github/workflows/api-tests.yml` runs on every push/PR to `main` and on
manual dispatch:

1. Checks out the repo
2. Installs dependencies from `requirements.txt`
3. Runs `pytest` (reads `OPENWEATHER_API_KEY` from a repo secret)
4. Uploads `reports/` as a build artifact
5. Publishes a JUnit test summary on the PR/run page

To enable the weather tests in CI, add a repository secret named
`OPENWEATHER_API_KEY` under **Settings → Secrets and variables → Actions**.

## Extending to another API

1. Add the new base URL to `BASE_URLS` in `tests/test_api.py`.
2. Create `tests/test_<name>.yaml`.
3. Push — CI picks it up automatically.
