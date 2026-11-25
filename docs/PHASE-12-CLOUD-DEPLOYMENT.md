# Phase 12 — Cloud Deployment: Vercel + Render

## Target architecture

```text
User → HTTPS → Vercel (Next.js frontend)
                   │ /api/* rewrite
                   ▼
             Render (FastAPI + Swagger) → Render PostgreSQL
```

Vercel manages HTTPS for the frontend. Render manages HTTPS for the API. The browser calls the frontend's `/api/*` routes; Vercel securely proxies those requests to Render using `BACKEND_API_URL`. This keeps the API base URL out of application code and preserves the existing frontend request paths.

## Before starting

- [ ] Commit and push the current verified work to the production branch, `zk`.
- [ ] Confirm `python -m pytest` and `npm run build` still pass locally.
- [ ] Never commit `.env`, Google OAuth secrets, JWT secrets, or database passwords.
- [ ] Deploy the API/database first; its public URL is needed for Vercel and Google OAuth.

## A. Deploy FastAPI and PostgreSQL on Render

1. Create an account at [Render](https://render.com/) and connect GitHub.
2. Select **New** → **Blueprint** and select `Zain-Khan05/bugsentinel-ai`, branch `zk`.
3. Render reads the repository's `render.yaml`. Create the Blueprint and wait for both `bugsentinel-api` and `bugsentinel-db` to be provisioned.
   The Blueprint explicitly tracks `zk` and has automatic deployment enabled: a new push to `zk` redeploys the API.
4. Open the `bugsentinel-api` service → **Environment**. Set these values:

| Key | Value |
| --- | --- |
| `JWT_SECRET` | A newly generated high-entropy value; for example `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ADMIN_PASSWORD` | A strong non-default administrator password |
| `DEVELOPER_PASSWORD` | A strong non-default demo developer password |
| `FRONTEND_URL` | Leave temporary for now; replace with the final Vercel HTTPS URL in section B |
| `CORS_ORIGINS` | The final Vercel HTTPS URL, for example `https://bugsentinel-ai.vercel.app` |
| `ALLOWED_HOSTS` | The API hostname only, for example `bugsentinel-api.onrender.com` — no `https://` |
| `GOOGLE_CLIENT_ID` | Existing Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Existing Google OAuth client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | `https://YOUR-RENDER-API.onrender.com/api/v1/auth/google/callback` |

5. Copy the API URL, such as `https://bugsentinel-api.onrender.com`.
6. Verify these URLs return HTTPS responses:

```text
https://YOUR-RENDER-API.onrender.com/api/v1/health
https://YOUR-RENDER-API.onrender.com/docs
```

Do not expose Render's database connection string in Vercel or in client-side variables. `render.yaml` injects it into the API service only.

## B. Deploy Next.js on Vercel

1. Create an account at [Vercel](https://vercel.com/) and import the same GitHub repository. Choose `zk` as the production branch during import, or set it afterwards in **Settings** → **Environments** → **Production** → **Branch Tracking**.
2. In **Configure Project**, set **Root Directory** to `frontend`.
3. Leave the framework preset as **Next.js**.
4. Under **Environment Variables**, set this build-time variable for Production and Preview:

| Key | Value |
| --- | --- |
| `BACKEND_API_URL` | `https://YOUR-RENDER-API.onrender.com` |

5. Deploy. Copy the Vercel production URL, such as `https://bugsentinel-ai.vercel.app`.
6. Return to Render and set both `FRONTEND_URL` and `CORS_ORIGINS` to that exact Vercel URL. Save changes and allow Render to redeploy.

## C. Update Google OAuth for production

In Google Cloud Console → **Google Auth Platform** → **Clients** → your web OAuth client:

1. Add this **Authorized redirect URI**:

```text
https://YOUR-RENDER-API.onrender.com/api/v1/auth/google/callback
```

2. Add this **Authorized JavaScript origin**:

```text
https://YOUR-VERCEL-APP.vercel.app
```

Keep the localhost entries as well, so local development continues working. Save the client configuration.

## Phase 12 verification checklist

- [ ] Vercel site opens over `https://` with no certificate warning.
- [ ] Render `/api/v1/health` returns `healthy` over `https://`.
- [ ] Render `/docs` opens the Swagger UI over `https://`.
- [ ] Select **Open Swagger** from the Vercel dashboard; it opens through the Vercel-to-Render proxy.
- [ ] Register a fresh test account; fields start empty and login succeeds.
- [ ] Submit a source scan from the Vercel UI and confirm its result appears.
- [ ] Use **Sign in with Google** and confirm the callback returns to the Vercel dashboard.
- [ ] Change the logged-in password and sign in again with the new password.
- [ ] In browser DevTools → Network, confirm frontend API requests use `/api/v1/...`, not a hard-coded localhost URL.
- [ ] Record the Vercel URL, Render API URL, Swagger URL, and screenshots for capstone evidence.

## Free-tier note

The free tiers are good for a capstone demonstration, not production. Render free services may sleep while idle, so the first request can be slow. Vercel Hobby is designed for personal/non-commercial projects. See the providers' current documentation before a final evaluation demo.

## Current production branch strategy

- `zk` is the repository default and production branch.
- Test `zk` locally and with a manual Jenkins **Build Now** run before pushing it.
- Render tracks `zk` only, so it rebuilds the API/database integration after each `zk` push.
- Vercel Production tracks `zk` only, so it rebuilds the live Next.js frontend after each `zk` push.
- If you later create `staging` and `master`, update both provider branch settings after the new release process has been tested.
