# Command contract (KavoshStart CI-8). CI runs setup/check; selected T2 heavy checks are incremental.
# TODO(kavosh): implement applicable targets. For a genuinely inapplicable operation,
# print N/A with its reviewed reason; never substitute a no-op for missing tests.
.PHONY: setup lint test build check check-full package

setup:
	@echo "TODO(kavosh): install dependencies" && exit 1

lint:
	@echo "TODO(kavosh): run linters" && exit 1

test:
	@echo "TODO(kavosh): run tests" && exit 1

build:
	@echo "TODO(kavosh): build" && exit 1

check: lint test build

# Selected T2 integration/release checks only; CI already ran make check in a preceding step.
# Implement a real suite or an explicit owner-reviewed N/A reason before first use.
check-full:
	@echo "TODO(kavosh): relevant integration checks or justified N/A" && exit 1

# runtime none/desktop only (release.yml has package: true): write release files to dist/.
# Server projects: delete this target.
package: build
	@echo "TODO(kavosh): write release files to dist/" && exit 1
