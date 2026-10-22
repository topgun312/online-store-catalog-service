BACKEND_DIR := backend
BOT_DIR := bot
FRONTEND_DIR := frontend

.DEFAULT_GOAL := help

.PHONY: help lint test api bot frontend migrate infra-up infra-down up down logs scale scale3 set-webhook seed seed-clear seed-images seed-docker seed-image-docker

help: ## list available commands
	@grep -E '^[a-z0-9-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

lint: ## run linters (ruff, black, isort --fix) in backend and bot
	@status=0; \
	$(MAKE) -C $(BACKEND_DIR) lint || status=$$?; \
	$(MAKE) -C $(BOT_DIR) lint || status=$$?; \
	exit $$status

test: ## run backend tests
	$(MAKE) -C $(BACKEND_DIR) test

api: ## run backend API
	$(MAKE) -C $(BACKEND_DIR) api

bot: ## run telegram bot locally (without Docker)
	cd $(BOT_DIR) && uv run python main.py

frontend: ## run frontend dev server (Next.js)
	cd $(FRONTEND_DIR) && npm run dev

migrate: ## apply database migrations
	$(MAKE) -C $(BACKEND_DIR) migrate

seed: ## load test data (3 categories + 20 products)
	$(MAKE) -C $(BACKEND_DIR) seed

seed-clear: ## remove the loaded test data
	$(MAKE) -C $(BACKEND_DIR) seed-clear

seed-images: ## upload placeholder images for seeded products into MinIO
	$(MAKE) -C $(BACKEND_DIR) seed-images

seed-docker: ## load test data into the docker compose PostgreSQL
	docker compose exec -T postgres psql -U postgres -d catalog_db -v ON_ERROR_STOP=1 \
		< backend/scripts/seed_test_data.sql

seed-image-docker: ## upload placeholder images into the docker compose MinIO
	docker compose exec -T backend /app/.venv/bin/python scripts/upload_seed_images.py

infra-up: ## start dev infrastructure (postgres + minio + redis)
	$(MAKE) -C $(BACKEND_DIR) infra-up

infra-down: ## stop dev infrastructure
	$(MAKE) -C $(BACKEND_DIR) infra-down

up: ## build & run the full stack (gateway + redis + bot)
	docker compose --profile bot up -d --build

down: ## stop the full stack (keep volumes)
	docker compose --profile bot down

logs: ## tail logs of all compose services
	docker compose --profile bot logs -f --tail=100

scale: ## build & run with replicas: backend=3, frontend=2, bot=2
	docker compose --profile bot up -d --build --scale backend=3 --scale frontend=2 --scale bot=2

scale3: ## stateless check: 3 backend replicas without bot
	docker compose up -d --build --scale backend=3

set-webhook: ## register Telegram webhook via one-shot bot-init
	docker compose --profile bot run --rm bot-init
