# BugSentinel AI

DevSecOps prototype for bug-risk prediction, code-quality checks and security findings. The UI is built with **Next.js 16 (React + TypeScript)**; the analysis API is built with FastAPI.

## Start

```powershell
# Create a local .env file (it is ignored by Git) with JWT_SECRET and passwords.
docker compose up --build
```

Open `https://localhost` (accept the local certificate warning) or `https://localhost/docs` for Swagger. Default user: `developer@example.com` / `ChangeMe123!`.

Docker Desktop must be running. The Nginx HTTPS configuration expects local certificate files in `nginx/certs/`; do not commit certificates or `.env` files.

For frontend-only development, run `npm install` and `npm run dev` from the `frontend` folder. The Next.js UI expects the FastAPI API at `http://localhost:8000` when run separately; set `NEXT_PUBLIC_API_URL=http://localhost:8000` before starting it.

## Local development architecture

```text
Next.js (localhost:3000) → FastAPI (localhost:8000) → SQLite/PostgreSQL
Docker deployment: Nginx → Next.js / FastAPI → PostgreSQL
```

See [the Phase 1 checklist](docs/PHASE-1-CHECKLIST.md) for the exact environment, dependency, Git, and GitHub setup steps.

## Capstone evidence

- `Jenkinsfile`: testing, SAST, Docker build/scan stages.
- `docker-compose.yml`: API, PostgreSQL, Nginx and HTTPS.
- `tests/`: Pytest unit/API tests and optional Selenium test.
- `postman/`: importable Postman collection.
- `.github/workflows/ci.yml`: GitHub CI workflow.
