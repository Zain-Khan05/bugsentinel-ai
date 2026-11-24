# BugSentinel AI

DevSecOps prototype for bug-risk prediction, code-quality checks and security findings. The UI is built with **Next.js 14 (React + TypeScript)**; the analysis API is built with FastAPI.

## Start

```powershell
Copy-Item .env.example .env
./scripts/new-dev-certificate.ps1
docker compose up --build
```

Open `https://localhost` (accept the local certificate warning) or `https://localhost/docs` for Swagger. Default user: `developer@bugsentinel.local` / `ChangeMe123!`.

Docker Desktop must be running. The certificate script creates a local self-signed development certificate; use a real CA-issued certificate such as Let's Encrypt in cloud deployment.

For frontend-only development, run `npm install` and `npm run dev` from the `frontend` folder. The Next.js UI expects the FastAPI API at `http://localhost:8000` when run separately; set `NEXT_PUBLIC_API_URL=http://localhost:8000` before starting it.

## Local development architecture

```text
Next.js (localhost:3000) → FastAPI (localhost:8000) → SQLite/PostgreSQL
Docker deployment: Nginx → Next.js / FastAPI → PostgreSQL
```

See [the Phase 1 checklist](docs/PHASE-1-CHECKLIST.md) for the exact environment, dependency, Git, and GitHub setup steps.

## Capstone evidence

- `Jenkinsfile`: testing, SAST, Docker build/scan and Kubernetes deploy stages.
- `docker-compose.yml`: API, PostgreSQL, Nginx and HTTPS.
- `k8s/app.yaml`: Kubernetes deployment/service/ingress.
- `tests/`: Pytest unit/API tests and optional Selenium test.
- `postman/`: importable Postman collection.
- `.github/workflows/ci.yml`: GitHub CI workflow.
