# Major-version migration: provider-neutral UI and private GitHub-hosted CI

**Breaking change.** This is a migration guide for the planned next major release, **not** an announcement that the release tag exists. Upgrade consumers only after a stable release in their own approved PR.

1. **UI manifest:** for `ui.kind != none`, declare `"designSystem": {"package": "<selected-package>", "version": "1.2.3"}` under `ui`. Replace any previous provider-specific key locally; never publish its actual value in the public standard. For a custom UI without a versioned package, use `ui.exceptionADR`; for `ui.kind=none`, use `designSystem: null`.
2. **CI runner:** set `ci.runner: github-hosted` for private GitHub Actions jobs. Remove private self-hosted labels/capacity/trust properties and disable any self-hosted job paths through an owner-authorized change in the consuming repository. `none` remains the no-Actions T1/static profile.
3. **Billing:** private GitHub-hosted jobs may consume shared quota. The owner must authorize one bounded manual `workflow_dispatch` tied to an exact current PR/head/ref; a manifest alone is not authorization.
4. **Tests and evidence:** regenerate templates, reconcile workflow inputs and run exact-source tests. Source-only hosted CI does not prove access to protected private Test/Production or product acceptance. Keep immutable deployment identity, required checks and environment-specific gates.
5. **Third parties:** assess component maturity/TCO, license/NOTICE, distribution and any network-source duties; maintain release-scoped inventory/SBOM and legal review for material unresolved rights in the consumer repository.

Earlier pinned consumers remain bound to their existing release until explicitly upgraded. Never use `main` or a PR head as a consumer's published standard version.
