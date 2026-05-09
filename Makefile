.PHONY: check backend-test frontend-build compose-config e2e-demo

check:
	bash scripts/check.sh

backend-test:
	cd services/api && pytest

frontend-build:
	cd apps/web && npm run build

compose-config:
	docker compose config

e2e-demo:
	python3 scripts/e2e_demo.py
