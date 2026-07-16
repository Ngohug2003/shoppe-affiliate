COMPOSE = docker compose

.PHONY: build up down restart logs logs-api ps shell migrate migration create-admin test test-cov lint format typecheck check clean

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f

logs-api:
	$(COMPOSE) logs -f api

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec api bash

migrate:
	$(COMPOSE) exec api alembic upgrade head

migration:
	@test -n "$(name)" || (echo 'Usage: make migration name="description"' && exit 1)
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(name)"

create-admin:
	$(COMPOSE) exec api python -m app.scripts.create_admin

test:
	$(COMPOSE) run --rm -e APP_ENV=test api pytest -v

test-cov:
	$(COMPOSE) run --rm -e APP_ENV=test api pytest --cov=app --cov-report=term-missing

lint:
	$(COMPOSE) run --rm api ruff check .

format:
	$(COMPOSE) run --rm api ruff format .

typecheck:
	$(COMPOSE) run --rm api mypy app

check: lint typecheck test

clean:
	@echo "WARNING: this deletes the development PostgreSQL volume."
	$(COMPOSE) down -v
