# Phase 8 — Docker deployment

## Container architecture

```text
Browser (localhost:8081) → Nginx → Next.js frontend / FastAPI API → PostgreSQL
Google callback (localhost:8000) → FastAPI → frontend redirect (localhost:8081)
```

## Before starting

Ensure your ignored root `.env` includes:

```text
JWT_SECRET=your-long-random-secret
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:3000
POSTGRES_PASSWORD=choose-a-local-development-database-password
```

Docker Compose overrides `FRONTEND_URL` to `http://localhost:8081` for the container stack. In Google Cloud Console, also add `http://localhost:8081` to authorized JavaScript origins.

## Run the stack

```cmd
docker compose up --build
```

Open:

- Application: `http://localhost:8081`
- Swagger: `http://localhost:8081/docs`
- Direct API health check: `http://localhost:8000/api/v1/health`

## Verification checklist

- [ ] `docker compose up --build` completes without errors.
- [ ] `docker compose ps` shows API, frontend, database, and Nginx running/healthy.
- [ ] Application opens at `http://localhost:8081`.
- [ ] Swagger opens at `http://localhost:8081/docs`.
- [ ] Login and source-code scan work through Nginx.
- [ ] Google Sign-In returns to the Docker-served dashboard.
- [ ] `docker compose down` then `docker compose up` preserves scan history in PostgreSQL.

## Stop the stack

```cmd
docker compose down
```

The named PostgreSQL volume is kept. Use `docker compose down -v` only when you intentionally want to delete all local database data.
