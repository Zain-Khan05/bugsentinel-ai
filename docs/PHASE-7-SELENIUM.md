# Phase 7 — Selenium browser tests

## What is covered

- Successful email/password login opens the dashboard.
- Invalid login shows an error message.
- Source submission renders a risk report.
- Sign out returns the user to the login screen.

## Run locally

Start the backend in terminal 1:

```cmd
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Start the frontend in terminal 2:

```cmd
cd frontend
npm run dev
```

Run Selenium in terminal 3 from the project root:

```cmd
.venv\Scripts\activate
set RUN_SELENIUM=1
set APP_URL=http://localhost:3000
python -m pytest -v tests/test_ui_selenium.py
```

Selenium Manager downloads or locates a compatible ChromeDriver automatically. Keep Google Chrome installed and close other test browser windows before running.
