.PHONY: help up down logs ps build parse-fsc clean test test-e2e test-e2e-real

help:
	@echo "Targets:"
	@echo "  make up         - docker compose up --build -d"
	@echo "  make down       - docker compose down"
	@echo "  make logs       - tail logs from all services"
	@echo "  make ps         - docker compose ps"
	@echo "  make build      - docker compose build"
	@echo "  make parse-fsc  - regenerate data/fsc_catalog.json"
	@echo "  make test       - run all python unit tests"
	@echo "  make clean      - down + remove volumes"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

build:
	docker compose build

parse-fsc:
	python3 scripts/parse_fsc_pdf.py \
		--input "AV_FSCClassAssignment._151007.pdf" \
		--output data/fsc_catalog.json

test:
	cd packages/shared && python3 -m pytest -q

test-e2e:
	cd apps/web && npx playwright test --project=mock --project=real-api

test-e2e-real:
	docker compose up --build -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	cd apps/web && npx playwright test --project=real
	docker compose down

clean:
	docker compose down -v
