# Runbook — deploy {{NAME}}

Pull-based (KavoshStart DEP-1…6): every 5 minutes the server looks for a newer tag and deploys itself.

```text
/opt/kavosh/{{SLUG}}/
  repo.git/            mirror (fetch only)
  releases/vX.Y.Z/     clean export per version (last 3 kept)
  shared/.env          configuration + secrets (outside every release)
  current -> releases/vX.Y.Z
```
Order per deploy: export → **backup** → **migrate** → build + up → health check → (failure) app rollback.
The database is **never** restored automatically.

## New server (once)
1. Install Docker + compose plugin, git, curl.
2. Add a **read-only deploy key** for `{{REPO}}` (Settings → Deploy keys) or use the KavoshRepo mirror URL.
3. `mkdir -p /opt/kavosh/{{SLUG}}/shared /etc/kavosh/{{SLUG}}` and create `shared/.env` from `.env.example`.
4. Copy `deploy/deploy.env.example` to `/etc/kavosh/{{SLUG}}/deploy.env`; set `CHANNEL`, `MIGRATE_CMD`, `BACKUP_CMD`.
5. `install -m 0755 deploy/kavosh-deploy.sh /usr/local/bin/kavosh-deploy-{{SLUG}}`
6. Production only: `echo v0.1.0 > /etc/kavosh/{{SLUG}}/pin`
7. Copy `deploy/kavosh-deploy.service` and `.timer` to `/etc/systemd/system/`, then `systemctl enable --now kavosh-deploy.timer`.

## Release to production
`echo vX.Y.Z > /etc/kavosh/{{SLUG}}/pin` — the next timer run deploys it. Verify: `curl -s <HEALTH_URL>`.

## When a deploy fails
- **Before migration** (backup or export failed): nothing changed. Fix the cause; the next run retries.
- **Migration failed:** the app still runs the previous version. Inspect the database. If it is inconsistent,
  restore the backup taken just before (see BACKUP_CMD), then fix forward with a new tag.
- **Health check failed after migration:** the script restarts the previous app version, which works because
  migrations are expand-only (DEP-5). Fix forward with a new tag. Only restore the backup if data is damaged.
- **Rollback failed:** `ls /opt/kavosh/{{SLUG}}/releases`, start the last good one by hand:
  `cd releases/<v> && KAVOSH_VERSION=<v> docker compose -p {{SLUG}} up -d`.

## Expand / contract (DEP-5)
A release may only **add** (tables, nullable columns, indexes) or change code to stop using something.
Removing or renaming what the previous release uses happens in a **later** release, once no running version needs it.

## Logs
`journalctl -u kavosh-deploy.service` and `/var/log/kavosh/{{SLUG}}-deploy.log`.
