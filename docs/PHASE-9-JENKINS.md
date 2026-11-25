# Phase 9 — Jenkins CI/CD

## Goal

Use Jenkins as the project CI server. Every branch build validates the backend, frontend and Docker configuration before code is promoted through the required branch flow:

```text
feature branch → zk → staging → master
```

Jenkins validates builds; it does **not** automatically merge or push branches. Pull requests and review remain the approval gate.

## What the pipeline does

The root `Jenkinsfile` runs these stages:

1. Checkout the selected branch.
2. Install Python dependencies and run backend unit/API tests with coverage.
3. Install frontend dependencies with `npm ci`, type-check and build Next.js.
4. Validate `docker-compose.yml` syntax.
5. Build the FastAPI Docker image.
6. Scan the image with Trivy for high/critical vulnerabilities.
7. Print the correct promotion action for `zk`, `staging`, or `master`.

The Selenium suite is intentionally not part of every Jenkins run because it needs a real browser and running web services. It remains a separate Phase 7 end-to-end check.

## Jenkins prerequisites

Use a Linux Jenkins agent with these tools available to the Jenkins user:

- Git
- Python 3.12 or newer and `venv`
- Node.js 20 and npm
- Docker Engine with Docker Compose v2
- permission to use `/var/run/docker.sock`

Install Jenkins plugins:

- Pipeline
- Git
- GitHub Branch Source
- JUnit
- Coverage (provides `publishCoverage`)
- ANSI Color

## Jenkins job setup

1. In Jenkins, select **New Item** → **Multibranch Pipeline**.
2. Set the display name to `BugSentinel-AI`.
3. Add your GitHub repository as the branch source.
4. Add GitHub credentials if the repository is private.
5. Keep the script path as `Jenkinsfile`.
6. In branch discovery, include `zk`, `staging`, `master`, and pull requests.
7. Save, then select **Scan Multibranch Pipeline Now**.
8. Open the automatically discovered `zk` job and choose **Build Now**.

For a simple single-branch demonstration, create a **Pipeline** job instead, choose **Pipeline script from SCM**, select Git, and use branch specifier `*/zk`.

## GitHub webhook

After Jenkins is reachable on a public HTTPS URL, create a GitHub repository webhook:

- Payload URL: `https://YOUR-JENKINS-DOMAIN/github-webhook/`
- Content type: `application/json`
- Event: **Just the push event** (or push and pull request events)
- Enable SSL verification

For local Jenkins, use **Build Now**. GitHub cannot send webhooks to `localhost` directly.

## Verification checklist

- [ ] Jenkins discovers the `zk` branch.
- [ ] A `zk` build completes successfully.
- [ ] Jenkins shows JUnit results and `coverage.xml` as an artifact.
- [ ] Backend test, frontend verify, Compose validation and Docker build stages are green.
- [ ] Trivy scan runs and is visible in the console log.
- [ ] A push to `zk` triggers Jenkins after the webhook is configured publicly.
- [ ] Promotion is performed as a pull request: `zk → staging → master`.

## Evidence for the capstone

Capture screenshots of the Jenkins stage view, passing test result, coverage artifact, Docker build log and Trivy output. Together with the existing GitHub branch history, they demonstrate CI/CD and DevSecOps practice.
