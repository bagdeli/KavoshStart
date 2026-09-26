# Command contract (KavoshStart CI-8). CI runs only `make setup` and `make check`.
# TODO(kavosh): implement each target for the chosen stack.
.PHONY: setup lint test build check package

setup:
	@echo "TODO(kavosh): install dependencies" && exit 1

lint:
	@echo "TODO(kavosh): run linters" && exit 1

test:
	@echo "TODO(kavosh): run tests" && exit 1

build:
	@echo "TODO(kavosh): build" && exit 1

check: lint test build

# runtime none/desktop only (release.yml has package: true): write release files to dist/.
# Server projects: delete this target.
package: build
	@echo "TODO(kavosh): write release files to dist/" && exit 1
