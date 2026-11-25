# BugSentinel AI

DevSecOps prototype for bug-risk prediction, code-quality checks and security findings. The UI is built with **Next.js 16 (React + TypeScript)**; the analysis API is built with FastAPI.

## Start

```powershell
# Create a local .env file (it is ignored by Git) with JWT_SECRET and passwords.
docker compose up --build
```

Open `http://localhost:8081` or `http://localhost:8081/docs` for Swagger. Default user: `developer@example.com` / `ChangeMe123!`.

Docker Desktop must be running. The local Docker stack uses HTTP at port 8081; configure HTTPS with a real certificate during cloud deployment. Do not commit `.env` files.

For frontend development, run `npm install` and `npm run dev` from the `frontend` folder. Next.js proxies `/api/*` requests to FastAPI at `http://localhost:8000` by default; set the local `BACKEND_API_URL` environment variable only if your backend uses another address.

## Local development architecture

```text
Next.js (localhost:3000) → FastAPI (localhost:8000) → SQLite/PostgreSQL
Docker deployment: Nginx (localhost:8081) → Next.js / FastAPI → PostgreSQL
```

See [the Phase 1 checklist](docs/PHASE-1-CHECKLIST.md) for the exact environment, dependency, Git, and GitHub setup steps.
See [the Docker guide](docs/PHASE-8-DOCKER.md) for container setup and verification.
See [the Jenkins guide](docs/PHASE-9-JENKINS.md) for CI/CD setup, branch promotion and webhook verification.
See [the security hardening guide](docs/PHASE-10-SECURITY.md) for implemented controls, scanning policy and verification.
See [the GitHub webhook guide](docs/PHASE-11-WEBHOOKS.md) for automatic Jenkins builds from `zk` pushes.
See [the cloud deployment guide](docs/PHASE-12-CLOUD-DEPLOYMENT.md) for Vercel + Render deployment and production OAuth configuration.

## Capstone evidence

- `Jenkinsfile`: backend tests, frontend verification, Docker build and Trivy container scanning.
- `docker-compose.yml`: API, PostgreSQL, Nginx and HTTPS.
- `tests/`: Pytest unit/API tests and optional Selenium test.
- `postman/`: importable Postman collection.
- `.github/workflows/ci.yml`: GitHub CI workflow.

## API documentation and Postman

FastAPI provides interactive Swagger documentation at `http://localhost:8000/docs`. Select **Authorize** and paste `Bearer <your-JWT>` to call protected scan endpoints. Import `postman/BugSentinel.postman_collection.json` into Postman, run **Login and save JWT**, then run the scan requests in order.
