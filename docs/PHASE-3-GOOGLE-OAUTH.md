# Phase 3 — Google Sign-In setup

## What is implemented

- `GET /api/v1/auth/google/login` redirects the user to Google using OAuth authorization-code flow.
- `GET /api/v1/auth/google/callback` validates the OAuth state, exchanges the code server-side, verifies the Google profile, links/creates a local account, and redirects with an application JWT.
- The Next.js login page includes **Continue with Google**.

## Local configuration

Create a local `.env` file in the project root. Never commit this file.

```text
JWT_SECRET=replace-with-a-long-random-value
GOOGLE_CLIENT_ID=paste-your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=paste-your-google-oauth-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

## Create Google credentials

1. Open Google Cloud Console and create/select a project.
2. Configure the OAuth consent screen as **External** for development, then add your Google account as a test user.
3. Create an **OAuth client ID** of type **Web application**.
4. Add `http://localhost:3000` as an authorized JavaScript origin.
5. Add `http://localhost:8000/api/v1/auth/google/callback` as an authorized redirect URI exactly.
6. Copy the client ID and client secret into the local `.env` file.
7. Restart FastAPI and Next.js.

## Verification checklist

- [ ] Clicking **Continue with Google** opens Google account selection.
- [ ] Google returns to `/oauth/callback` after consent.
- [ ] The app opens the dashboard with a JWT session.
- [ ] Refreshing the dashboard retains the session.
- [ ] An invalid or reused OAuth state is rejected.
- [ ] `python -m pytest tests/test_analyzer.py tests/test_api.py` passes.
