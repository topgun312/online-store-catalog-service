UV := uv run

# run linters
lint:
	$(UV) isort .
	$(UV) black .
	$(UV) ruff check . --config=pyproject.toml --fix

# run tests
test:
	$(UV) pytest -vv -p no:warnings

# run API
api:
	$(UV) python -m src

# apply migrations
migrate:
	$(UV) alembic upgrade head

# apply migrations and load test data (3 categories + 20 products) into dev postgres
seed: migrate
	PGPASSWORD=postgres psql -h localhost -U postgres -d catalog_db -v ON_ERROR_STOP=1 -f scripts/seed_test_data.sql

# remove the test data loaded by `make seed`
seed-clear:
	PGPASSWORD=postgres psql -h localhost -U postgres -d catalog_db -v ON_ERROR_STOP=1 -f scripts/seed_test_data_clear.sql

# upload placeholder images for the seeded products into MinIO
seed-images:
	$(UV) python scripts/upload_seed_images.py

# dev infrastructure (postgres + minio)
infra-up:
	docker compose -f deploy/docker-compose.dev.yaml up -d

infra-down:
	docker compose -f deploy/docker-compose.dev.yaml down
