# Runbook — deploy {{NAME}}

Pull-based (KavoshStart DEP-1…4): the server checks for new tags every 5 minutes and deploys itself.

## New server (once)
1. Install Docker + compose plugin and git.
2. Create a **read-only deploy key** for `{{REPO}}` (Settings → Deploy keys), put the private key in `/root/.ssh/`.
3. `git clone <REPO_URL> /opt/kavosh/{{SLUG}}` then create `/opt/kavosh/{{SLUG}}/.env` from `.env.example`.
4. `mkdir -p /etc/kavosh/{{SLUG}} && cp deploy/deploy.env.example /etc/kavosh/{{SLUG}}/deploy.env` and edit `CHANNEL`.
5. Production only: `echo v0.1.0 > /etc/kavosh/{{SLUG}}/pin`.
6. `cp deploy/kavosh-deploy.service deploy/kavosh-deploy.timer /etc/systemd/system/ && systemctl enable --now kavosh-deploy.timer`

## Release to production
`echo vX.Y.Z > /etc/kavosh/{{SLUG}}/pin` — the next timer run deploys it. Check: `curl -s <HEALTH_URL>`.

## Roll back
`echo <previous version> > /etc/kavosh/{{SLUG}}/pin` (production) — or on test, fix forward with a new rc tag.
The script already rolls back automatically when the health check fails.

## Logs
`journalctl -u kavosh-deploy.service` and `/var/log/kavosh/{{SLUG}}-deploy.log`.
