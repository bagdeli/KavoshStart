.PHONY: setup lint test build check conformance

setup:
	@python3 --version

lint:
	python3 scripts/public_source_guard.py
	python3 tooling/rule_registry.py --check
	python3 tooling/sync_pins.py --check
	python3 tooling/build_workflows.py --check
	python3 -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('**/*.json',recursive=True)]"
	for f in scripts/*.sh templates/common/.githooks/* templates/runtime/server/deploy/*.sh; do bash -n "$$f" || exit 1; done

test:
	python3 -m unittest discover -s tooling/tests
	python3 tooling/test_templates.py

build:
	@true

check: lint test build

conformance:
	python3 tooling/test_cross_domain.py --junit $${KAVOSH_CONFORMANCE_REPORT:-cross-domain.xml}
