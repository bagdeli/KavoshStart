# Executable capability boundary fixtures

`make conformance` complements `make check`: it exercises six isolated consumer
boundaries with real tools, not just YAML markers or a copied pass string. It
adds no new universal product rules. Each fixture validates its composable
capability declaration, runs a working control and rejects seeded defects.

| Profile | Executed outcome | Deliberate counterexamples | Not claimed |
| --- | --- | --- | --- |
| package/library + monorepo | npm workspace import, pack, offline install into an independent consumer | broken workspace API and modified installed API | all package managers or package signing |
| persistent data / migration | actual SQLite schema expansion, retained data and transaction rollback | missing retired column, NOT NULL violation | PostgreSQL/MySQL or production migration rehearsal |
| infrastructure/IaC | actual Terraform local state apply and idempotent plan with built-in terraform_data | changed desired state and forbidden environment | cloud providers, real resources or deployment permission |
| browser UI | actual Chrome + Playwright, 320/1280 viewport, RTL, label, Tab/Enter, feedback, safe text rendering | innerHTML injection and overflowing layout | human UAT, screen-reader certification or all browsers |
| desktop artifact | build a Python zipapp, remove source, launch the distributed artifact | broken archive entry point | native signing, GUI interaction or every operating system |
| CMS/WordPress | PHP executing the actual WordPress core hook engine | missing registration and unsafe output | full site installation, database/authentication or WooCommerce |

All work is in fresh temporary directories. Terraform uses only its built-in
resource: no backend, external provider, provisioner, cloud account or live
infrastructure. WordPress loads only its two core hook implementation files;
there is no site, installer or database. Browser network requests are blocked.
Child processes do not inherit product credentials or user package-manager
configuration. Historical dependency versions are test fixtures, not production
upgrade recommendations.

## Run

Use Python 3.10+, Node/npm, PHP CLI and Chrome/Chromium. Install the test-only
Playwright driver from `tooling/conformance-requirements.txt`. Prepare Terraform
and the WordPress core hook files in an **empty disposable** directory:

```bash
export KAVOSH_CONFORMANCE_DEPS="$(mktemp -d)"
bash tooling/prepare_conformance.sh
export KAVOSH_TERRAFORM="$KAVOSH_CONFORMANCE_DEPS/terraform"
export KAVOSH_WORDPRESS_ROOT="$KAVOSH_CONFORMANCE_DEPS/wordpress"
# Optional: KAVOSH_CHROME=/path/to/chrome
make conformance
```

The preparer refuses a nonempty directory. It verifies Terraform 1.9.8 against
the SHA-256 published in HashiCorp's versioned checksum manifest, and the exact
WordPress 6.8.3 archive against WordPress's published SHA-1 archive pin. Only two
specified hook files are unpacked. The isolated runner verifies the installed
engines by execution; it does not install either product as a service.

Sources for the fixture interfaces and pins:
- https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_SHA256SUMS
- https://developer.hashicorp.com/terraform/language/resources/terraform-data
- https://wordpress.org/wordpress-6.8.3.tar.gz.sha1
- https://developer.wordpress.org/reference/functions/add_filter/
- https://developer.wordpress.org/reference/functions/apply_filters/
- https://playwright.dev/python/docs/input

`self-check` runs all profiles in the existing `required` job and retains the
actual JUnit report, including failures. A missing tool, timeout or setup failure
fails the job; none is converted to a skip or passing result. Core unit/template
checks remain available without these extra engines. For an explicitly partial
local run, use `--profiles package migration desktop`; that is not full conformance.

Every result is fed through the shared JUnit assertion adapter. A fixture whose
negative control is not detected fails its overall result. These are regression
proofs for the stated fixture boundaries, not independently issued receipts,
product acceptance or evidence that a downstream application's tests are adequate.
