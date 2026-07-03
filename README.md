# API Test Automation Framework — Reqres

A lightweight, reusable Python framework for testing REST APIs. Test cases
are authored as YAML data (no Python required to add coverage), executed
with `pytest` + `requests`, and wired into GitHub Actions for CI on every
push/PR.

Demonstrated against [Reqres](https://reqres.in/) — a free mock user/auth API.

## Repository layout

```
tests/                    API test cases (YAML) + the generic pytest executor
framework/                Reusable client, loader, logger, assertion engine
docs/                     Test-case format & architecture docs
.github/workflows/        CI pipeline (GitHub only reads workflows from this path)
```

## Local setup

```bash
git clone <your-repo-url>
cd api-test-framework
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

### API key (required)

Reqres now requires an `x-api-key` header on every request. Get a free key
at **https://reqres.in/signup**, then:

```bash
cp .env.example .env
# edit .env and set REQRES_API_KEY=your_key_here
```

`conftest.py` loads `.env` automatically — no manual `export` needed. If no
key is found (in `.env`, the environment, or via `--api-key`), the test run
stops immediately with a clear message rather than failing 5 separate tests
with confusing 401s.

## Running the tests

```bash
pytest
```

By default, tests run against `https://reqres.in`. This produces:

- Console output (`-v`, one line per test case)
- `reports/report.html` — self-contained HTML report
- `reports/junit.xml` — JUnit XML for CI integration
- `reports/test_run.log` — full request/response log for debugging

Run a single test case with normal pytest filters:

```bash
pytest -k "Login successful"
```

## Configuring the base URL and API key

You don't have to edit any code to point the suite at a different host or
key. Both follow the same priority order:

**1. Command-line flag (highest priority)**
```bash
pytest --base-url https://reqres.in --api-key your_key_here
```

**2. `.env` file**
```bash
cp .env.example .env
# edit .env: set REQRES_API_KEY=... and optionally BASE_URL=...
pytest
```
`conftest.py` loads `.env` automatically via `python-dotenv`.

**3. Built-in default** — only `base_url` has one (`https://reqres.in`,
defined in `conftest.py::DEFAULT_BASE_URL`). There is no default API key;
if none is found, the run stops immediately with instructions instead of
producing five confusing 401 failures.

## Adding a test case

No Python needed — add an entry to `tests/test_reqres.yaml`. See
[`docs/writing-test-cases.md`](docs/writing-test-cases.md) for the full
schema and assertion syntax. Example:

```yaml
tests:
  - name: Get user details
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

`.github/workflows/api-tests.yml` runs on every push/PR to `main`, and can
also be triggered manually with `base_url` and `api_key` overrides
(**Actions → API Tests → Run workflow**). Each run:

1. Checks out the repo
2. Installs dependencies from `requirements.txt`
3. Runs `pytest`
4. Uploads `reports/` as a build artifact
5. Publishes a JUnit test summary on the run page

`api_key` is a manual-dispatch input, not a repo secret — type it into the
"Run workflow" form when triggering manually. Note this means it will be
visible in plain text in that run's log; for anything beyond demo/personal
use, switching it to a repo secret (**Settings → Secrets and variables →
Actions**) is the safer long-term option.
