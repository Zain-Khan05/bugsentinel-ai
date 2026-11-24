# Phase 6 — Unit and API tests

## Test coverage

- Analyzer security, JavaScript metrics, and multi-file summaries.
- Health, registration, duplicate registration, and password policy.
- JWT login and current-user profile.
- Missing and invalid JWT rejection.
- Scan ownership isolation between developer accounts.
- Admin-only audit authorization.
- Google OAuth behavior with and without server configuration.

## Run locally

```cmd
python -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

Open `htmlcov/index.html` after the command to view the local coverage report. `coverage.xml` and `test-results.xml` are produced for CI tools.
