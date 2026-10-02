# Local validation without GitHub Actions

Use this only when the manifest has `tier: "T1"`, `runtime: "static"`, `ci.runner: "none"`, and
`ci.monthlyMinutesBudget: 0`. KavoshStart scaffolding omits every GitHub Actions workflow for this profile.

Before each PR, run:

```bash
make setup
make check
```

Put a `## Local validation` section in the PR body with the commands, exit code, brief test/build summary, and
local runtime/tool versions. Keep credentials and secret values out of the output. A failed check or missing
validation record blocks merge. The profile has no CI status check to bypass; pull-request and branch protections
remain active. If GitHub reports an actual required check as failing, fix it instead of bypassing it.

For a browser-driven smoke test, use headless Chromium or Chrome already installed on the machine. If no supported
browser is installed, report `SKIP` and say which browser was absent. Store each test file's output separately under
`artifacts/smoke/<test-name>/`. On Windows, place the app and browser in a Job Object and close the whole process
tree in a `finally` cleanup path. Offline validation must not download browsers or dependencies.
