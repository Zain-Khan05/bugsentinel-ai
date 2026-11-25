# Phase 11 — GitHub Webhooks for Jenkins CI

## Goal

Automatically trigger the `BugSentinel-AI` Jenkins pipeline whenever code is pushed to the `zk` branch. This replaces manual **Build Now** runs and provides CI/CD evidence for the capstone.

```text
Developer push → GitHub webhook → HTTPS tunnel / cloud URL → Jenkins /github-webhook/ → BugSentinel-AI build
```

## Why localhost is not enough

GitHub's servers cannot call `http://localhost:8080` on your computer. Jenkins must be reachable through a public HTTPS URL. For local demonstration, use an HTTPS tunnel; after Phase 12, use the cloud Jenkins URL instead.

## Jenkins configuration

1. In Jenkins, select **Manage Jenkins** → **Plugins**.
2. Install the **GitHub** plugin and restart Jenkins if requested.
3. Open the `BugSentinel-AI` job → **Configure**.
4. Under **Build Triggers**, enable **GitHub hook trigger for GITScm polling**.
5. Save the job.

The Jenkins GitHub plugin listens at:

```text
https://YOUR-PUBLIC-JENKINS-URL/github-webhook/
```

For example, if a tunnel produces `https://example-tunnel.example`, the webhook URL is:

```text
https://example-tunnel.example/github-webhook/
```

## Local HTTPS tunnel

Use one HTTPS tunnel tool approved by your team, such as Cloudflare Tunnel or ngrok. Point it to your running Jenkins instance:

```text
http://localhost:8080
```

Keep the tunnel running while testing. Do not expose Jenkins broadly without authentication; the GitHub webhook endpoint is the only public route required for this phase.

## GitHub repository webhook

In `Zain-Khan05/bugsentinel-ai`:

1. Open **Settings** → **Webhooks** → **Add webhook**.
2. Set **Payload URL** to your public Jenkins webhook URL ending in `/github-webhook/`.
3. Set **Content type** to `application/json`.
4. Select **Just the push event**.
5. Set the webhook to **Active** and save.

The Jenkins GitHub plugin checks incoming notifications against GitHub before triggering matching jobs. If using a tunnel/relay that supports GitHub signature validation, configure the same high-entropy webhook secret in both GitHub and that receiver. Do not commit it or paste it into the Jenkinsfile.

## Verification

1. Make a harmless commit on `zk`, such as a documentation change.
2. Push it with `git push origin zk`.
3. Open GitHub → **Settings** → **Webhooks** → your webhook → **Recent Deliveries**.
4. Confirm the delivery returns HTTP `200`.
5. Open Jenkins and confirm a new `BugSentinel-AI` build starts automatically.
6. Confirm the build completes successfully and checked out the pushed commit SHA.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| GitHub delivery fails | Confirm the tunnel is running and the URL ends in `/github-webhook/`. |
| Delivery is 404 | Install/configure the Jenkins GitHub plugin and enable the job trigger. |
| Delivery is 200 but no build starts | Verify the job Git URL exactly matches `https://github.com/Zain-Khan05/bugsentinel-ai.git` and the trigger is enabled. |
| GitHub cannot reach the URL | `localhost` is not public; start a tunnel or wait for Phase 12 cloud deployment. |
| Jenkins has no GitHub trigger checkbox | Install the Jenkins **GitHub** plugin, not only the Git plugin. |

## Capstone evidence

Capture a screenshot of the GitHub webhook delivery marked successful and the Jenkins build started by that push. Together with the Jenkins Stage View, this demonstrates automated CI through webhooks.
