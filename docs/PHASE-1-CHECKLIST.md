# Phase 1 — Project Foundation

## Completed in the workspace

- [x] Git repository initialized locally.
- [x] Next.js frontend and FastAPI backend retained as separate services.
- [x] Docker Compose routes browser traffic through Nginx to Next.js and routes `/api/` to FastAPI.
- [x] Root and frontend environment-variable templates created.
- [x] Sensitive local files, dependencies, build output, and certificates ignored by Git.

## You need to complete locally

- [ ] In `frontend`, run `npm install` to install the supported, audit-fixed Next.js 16.4.6 and React 19 dependencies declared in `package.json`.
- [ ] In `frontend`, run `npm run build` successfully.
- [ ] Copy `.env.example` to `.env` and replace `JWT_SECRET` with a long random value.
- [ ] For separate local services, copy `frontend/.env.example` to `frontend/.env.local`.
- [ ] Start FastAPI at `http://localhost:8000` and confirm `http://localhost:8000/docs` works.
- [ ] Start Next.js at `http://localhost:3000` and confirm sign-in works.
- [ ] Configure Git identity, if required: `git config user.name "Your Name"` and `git config user.email "your@email.com"`.
- [ ] Create the first commit.
- [ ] Create an empty GitHub repository and add it as `origin`.
- [ ] Push the `main` branch to GitHub.

## Useful commands

```powershell
# Frontend
cd frontend
npm install
Copy-Item .env.example .env.local
npm run build
npm run dev

# Backend, from project root (requires Python installed)
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Git, from project root
git add .
git commit -m "chore: establish project foundation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/bugsentinel-ai.git
git push -u origin main
```
