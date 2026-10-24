# Runbook — deploy {{NAME}}

**Only when the project actually chooses the Kavosh pull-based deployer:** its project-scoped timer handles immutable *product* SemVer releases. A routine native upstream component update **only when this is already the owner's chosen deployment adapter and the component version is not pinned in product source/lock/image** does not require installing this deployer, an extra Test environment, a new project release/RC, or a new restore rehearsal. If the canonical product tracks the component, update the tracked reference and use the real product release path; do not create untracked server drift. Native update paths must verify their real version, affected integration and health; durable data changes still require an adequate recoverable backup. A persistent environment is not accepted merely because CI or a disposable Compose proof is green.

```text
/opt/kavosh/{{SLUG}}/
  repo.git/            mirror (fetch only)
  releases/vX.Y.Z/     clean export per version
  shared/.env          runtime configuration + secrets outside releases
  current -> releases/vX.Y.Z
/etc/kavosh/{{SLUG}}/
  deploy.env           non-secret operational configuration
  pin                  Production target only
```

Per deploy: fetch tags → prepare clean release → recovery gates → optional snapshot → migrate → build/pull artifact → start → exact local + canonical `/version` → independent local + canonical `/health` → activate `current`. The database is **never** restored automatically.

## New server — admission sequence (only for the selected standard deployer)

These steps apply to a selected canonical environment using this adapter, **not to every existing CMS/site or dependency update**. No separate Test VM/host is required. Production and Test share no sensitive data/credentials merely because they share hardware.

Do not point a canonical Test/Production name at an ad-hoc long-lived Compose project and “standardize later”. Temporary previews use unique project/data names and are not Kavosh Test/Production until this admission passes.

1. Install Docker + Compose plugin, git, curl and Python 3. Provision the dedicated runtime/deploy account.
2. Add a **read-only deploy key** for `{{REPO}}` or use the approved mirror.
3. Create `/opt/kavosh/{{SLUG}}/shared` and `/etc/kavosh/{{SLUG}}`; create `shared/.env` from the project runtime example with least-privilege permissions.
4. Copy `deploy/deploy.env.example` to `/etc/kavosh/{{SLUG}}/deploy.env` and set:
   - `DEPLOY_METHOD` to the manifest value;
   - distinct loopback `VERSION_URL` and `HEALTH_URL`;
   - `PUBLIC_BASE_URL` to the canonical environment origin used by the reverse proxy/DNS path;
   - migration/recovery commands where a database exists;
   - for `pull-image`, a real `ARTIFACT_VERIFY_CMD` that verifies immutable image/artifact provenance against `KAVOSH_VERSION` + `KAVOSH_SHA`.
5. Install the deployer:
   ```sh
   install -m 0755 deploy/kavosh-deploy.sh /usr/local/bin/kavosh-deploy-{{SLUG}}
   ```
6. Install **project-scoped** units. The source template filenames are generic, but the installed unit names are not:
   ```sh
   install -m 0644 deploy/kavosh-deploy.service /etc/systemd/system/kavosh-deploy-{{SLUG}}.service
   install -m 0644 deploy/kavosh-deploy.timer   /etc/systemd/system/kavosh-deploy-{{SLUG}}.timer
   systemctl daemon-reload
   ```
   Never install a shared `kavosh-deploy.service` / `kavosh-deploy.timer` name on a multi-project host.
7. Configure the canonical reverse proxy/DNS so `PUBLIC_BASE_URL/version` and `PUBLIC_BASE_URL/health` reach the stable loopback listener owned by this project. Do not proxy the canonical origin to a runner proof or temporary Compose stack.
8. Ensure an approved immutable SemVer target exists. Test requires a final or RC tag; Production requires the owner pin:
   ```sh
   echo vX.Y.Z > /etc/kavosh/{{SLUG}}/pin   # Production only
   ```
9. Start one deployment explicitly through the project unit, then enable the timer:
   ```sh
   systemctl start kavosh-deploy-{{SLUG}}.service
   systemctl enable --now kavosh-deploy-{{SLUG}}.timer
   ```
10. Run the admission/drift check using the same protected deploy environment:
    ```sh
    sudo bash -c 'set -a; . /etc/kavosh/{{SLUG}}/deploy.env; set +a; /usr/local/bin/kavosh-deploy-{{SLUG}} --verify-environment'
    ```
    Expected output starts with `ENVIRONMENT_CONFORMANCE=PASS`. Any missing layout/unit/timer, wrong `current`, non-SemVer target, wrong exact SHA/version, unhealthy app, or canonical-proxy mismatch is a **failed environment admission**.

Only after step 10 may this host be represented as the canonical Kavosh Test/Production environment.

## Continuous drift behavior

The timer does not silently exit when the target tag equals `current`. It re-checks exact local and canonical identity plus independent health. If the canonical proxy serves an older stack/image, or the runtime becomes unhealthy, the run fails with a drift finding. Green repository CI therefore cannot mask a stale persistent host.

Use the same read-only verifier whenever environment status is questioned:

```sh
sudo bash -c 'set -a; . /etc/kavosh/{{SLUG}}/deploy.env; set +a; /usr/local/bin/kavosh-deploy-{{SLUG}} --verify-environment'
```

## Pull-build versus pull-image

- `pull-build`: builds from the clean exported release directory and then starts it.
- `pull-image`: pulls the release image, **requires** `ARTIFACT_VERIFY_CMD`, and starts with `--no-build --pull never` only after that verification succeeds. Merely injecting `KAVOSH_SHA` into an old image is not provenance.

If registry/signature provenance cannot be verified, use `pull-build` or an ADR-backed custom deployment rather than weakening DEP-9.

## Release to Production

Write the exact approved SemVer tag to the pin; the next project-scoped timer run deploys it. Verify both identity and health, or run `--verify-environment`. A 200 response without exact version/SHA is not a successful deployment.

## T1/T2 expressly selected maintenance-window migration

Use only for a real product DB migration when T1 **or T2** explicitly selects `migrationMode: maintenance-window` and names an accepted ADR that documents downtime, migration/recovery, backup, restore test and rollback. No extra ADR or downtime mode applies merely because a mature upstream component updates itself. Configure `MAINTENANCE_STOP_CMD`. The timer cannot authorize this operation; an owner must directly run the deploy command for the exact tag:

```sh
sudo env DEPLOY_ACTOR="$USER" bash -c 'set -a; . /etc/kavosh/{{SLUG}}/deploy.env; set +a; /usr/local/bin/kavosh-deploy-{{SLUG}} --authorize-maintenance-window vX.Y.Z'
```

## When a deploy fails

- **Before migration**: running release remains unchanged.
- **Migration failed**: inspect the database; restore only with a separate owner-authorized recovery action.
- **Identity/health failed after start**: the application rolls back when the migration mode permits it. The database does not.
- **No-op drift check failed**: do not rebuild blindly. Compare `current`, the exact target tag/SHA, local endpoints and canonical proxy routing. A stale alternative Compose/image is an environment defect.
- **Rollback failed**: inspect `/opt/kavosh/{{SLUG}}/releases` and follow the incident runbook; do not repoint `current` to an unverified working tree.

## Revision-source consistency when a database migration exists

The expected revision must come directly from the actual checked-out migration graph, not a handwritten expected version. An optional read-only preflight is `python3 <KavoshStart>/scripts/check_migration_revision.py --source-command '["alembic", "heads"]'` for consumers using Alembic. It requires **exactly one valid source head**; malformed/empty or multiple heads, command errors and timeouts block the claimed proof. After an authorized migration, add `--applied-command '["alembic", "current"]'` and require exact equality. A command not run is NOT RUN, never PASS. This helper admits only reviewed Alembic `heads` and `current` read operations (not `upgrade`, `stamp` or arbitrary shell commands). Alembic may still load product `env.py`; it is NOT a sandbox and cannot prove DB credentials or script side effects are safe. It is not auto-installed and cannot replace real rollback/restore/security evidence. Another migration engine needs its own reviewed native adapter, not a fake constant output.

## Expand / contract (DEP-5/6)

For migrations using `expand-contract`, keep schema compatible across the release window. A **real durable-data migration** first checks its existing recoverable backup; for low-risk reversible work the standard deployer does **not** require a new PITR service, external backup provider or fresh restore drill, although any configured restore check must pass. High/destructive migrations require successful reviewed restore evidence and a fresh snapshot. For a non-migration upstream maintenance update, leave `MIGRATE_CMD` unset: the backup/migration commands never run. Database restore stays manual and owner-authorized.

## Logs

`journalctl -u kavosh-deploy-{{SLUG}}.service`,
`journalctl -u kavosh-deploy-{{SLUG}}.timer`, and
`/var/log/kavosh/{{SLUG}}-deploy.log`.
