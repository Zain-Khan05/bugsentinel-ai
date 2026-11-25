# Phase 10 — Security Hardening

## Controls implemented

- Replaced `python-jose` with maintained `PyJWT` for HS256 application tokens. This removes the `python-jose` and `ecdsa` vulnerability chain found by Trivy.
- Updated FastAPI and its Starlette dependency to current compatible releases.
- Added trusted-host protection. Local development allows only `localhost`, `127.0.0.1`, `testserver`, and the Docker API service by default. Cloud deployment must set `ALLOWED_HOSTS` to the real application domain.
- Restricted CORS to known local frontend origins, `GET`/`POST`/`OPTIONS` methods, and `Authorization`/`Content-Type` headers.
- Added API response headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and no-store caching for API responses.
- Added Nginx browser-facing headers: Content Security Policy framing/object restrictions, Permissions Policy, Cross-Origin Opener Policy, and cross-domain policy denial.
- Docker already runs the API as an unprivileged `appuser`, limits request bodies at Nginx, and keeps secrets out of images through `.dockerignore` and `.gitignore`.

## Dependency scan policy

Jenkins runs Trivy in reporting mode. It records high/critical findings without blocking a student-development build, so findings can be reviewed and remediated deliberately. Before a production release, change Trivy to `--exit-code 1` after reviewing accepted risks.

The base operating-system image can still report vulnerabilities that have no upstream fixed version at scan time. Mitigate them by rebuilding regularly with `docker build --pull`, applying patched base-image releases promptly, and documenting any temporary exceptions.

## Verification checklist

- [ ] `python -m pytest tests/test_analyzer.py tests/test_api.py` passes.
- [ ] The API test verifies headers and rejects an untrusted Host header with HTTP 400.
- [ ] `npm run typecheck` and `npm run build` pass in `frontend/`.
- [ ] `docker compose up --build` starts successfully.
- [ ] `docker compose ps` shows healthy services.
- [ ] Jenkins completes the Trivy scan and its result is retained in the console log.
- [ ] Cloud deployment sets `ALLOWED_HOSTS` to its actual domain and enables HTTPS (Phase 12).

## Demonstration notes

For the capstone presentation, show the passing security-header test, the Jenkins Trivy stage, the non-root Dockerfile `USER appuser`, Nginx rate limiting, ignored `.env`, and the Google OAuth/JWT authentication flow. These provide concrete DevSecOps evidence rather than only a security claim.
