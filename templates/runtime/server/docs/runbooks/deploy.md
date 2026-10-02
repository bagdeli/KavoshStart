# Runbook — deploy {{NAME}}

Pull-based (KavoshStart DEP-1…6): every 5 minutes the server looks for a newer tag and deploys itself.

```text
/opt/kavosh/{{SLUG}}/
  repo.git/            mirror (fetch only)
  releases/vX.Y.Z/     clean export per version (last 3 kept)
  shared/.env          configuration + secrets (outside every release)
  current -> releases/vX.Y.Z
```
Order per deploy: export → verify continuous recovery → risk-based snapshot when needed → migrate → build + up → health check → (failure) app rollback.
The database is **never** restored automatically.

## New server (once)
1. Install Docker + compose plugin, git, curl.
2. Add a **read-only deploy key** for `{{REPO}}` (Settings → Deploy keys) or use the KavoshRepo mirror URL.
3. `mkdir -p /opt/kavosh/{{SLUG}}/shared /etc/kavosh/{{SLUG}}` and create `shared/.env` from `.env.example`.
4. Copy `deploy/deploy.env.example` to `/etc/kavosh/{{SLUG}}/deploy.env`; set `CHANNEL`, `MIGRATE_CMD`, and failing-closed `BACKUP_HEALTHCHECK_CMD` and `RESTORE_TEST_CHECK_CMD`. The latter must verify recent successful restore-test evidence. Set `MIGRATION_RISK=high` or `destructive` for a fresh snapshot before high-risk changes, rewrites, or destructive changes; configure `BACKUP_CMD` for that snapshot.
5. `install -m 0755 deploy/kavosh-deploy.sh /usr/local/bin/kavosh-deploy-{{SLUG}}`
6. Production only: `echo v0.1.0 > /etc/kavosh/{{SLUG}}/pin`
7. Copy `deploy/kavosh-deploy.service` and `.timer` to `/etc/systemd/system/`, then `systemctl enable --now kavosh-deploy.timer`.

## Release to production
`echo vX.Y.Z > /etc/kavosh/{{SLUG}}/pin` — the next timer run deploys it. Verify: `curl -s <HEALTH_URL>`.

## T1 maintenance-window migration
Use only when the manifest selects `migrationMode: maintenance-window` and names an ADR that documents the maintenance window, tested recovery, backup, and rollback. Configure `MAINTENANCE_STOP_CMD` in `deploy.env` (for example, `docker compose -p {{SLUG}} stop`) so the old app is stopped after recovery checks and any required snapshot. The timer cannot authorize this operation: an owner must directly run the deploy command for the exact tag, for example:

```sh
sudo env DEPLOY_ACTOR="$USER" bash -c 'set -a; . /etc/kavosh/{{SLUG}}/deploy.env; set +a; /usr/local/bin/kavosh-deploy-{{SLUG}} --authorize-maintenance-window vX.Y.Z'
```

The script rejects a missing/mismatched tag, a non-T1 manifest, missing ADR evidence, or absent stop command. It leaves the service stopped for manual recovery after a failed incompatible migration; it never restores the database.

## When a deploy fails
- **Before migration** (backup or export failed): nothing changed. Fix the cause; the next run retries.
- **Migration failed:** with expand/contract, the previous app remains running. In a maintenance window the service remains stopped because compatibility is not assumed. Inspect the database. If it is inconsistent,
  assess recovery using the verified continuous backup/PITR and any risk-based snapshot; restore only through this runbook with separate owner authorization, then fix forward with a new tag.
- **Health check failed after migration:** the script restarts the previous app version, which works because
  migrations are expand-only (DEP-5). Fix forward with a new tag. Only restore the backup if data is damaged.
- **Rollback failed:** `ls /opt/kavosh/{{SLUG}}/releases`, start the last good one by hand:
  `cd releases/<v> && KAVOSH_VERSION=<v> docker compose -p {{SLUG}} up -d`.

## Expand / contract (DEP-5)
A release may only **add** (tables, nullable columns, indexes) or change code to stop using something.
Removing or renaming what the previous release uses happens in a **later** release, once no running version needs it.

## Logs
`journalctl -u kavosh-deploy.service` and `/var/log/kavosh/{{SLUG}}-deploy.log`.
