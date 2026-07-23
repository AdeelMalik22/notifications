UV := uv
COMPOSE := docker compose

.PHONY: install format lint types test django-check migrations-check check \
	up down logs migrate smoke

install:
	$(UV) sync --frozen --all-groups

format:
	$(UV) run ruff format .

lint:
	$(UV) run ruff format --check .
	$(UV) run ruff check .

types:
	$(UV) run mypy apps notifications tests manage.py

test:
	$(UV) run pytest

django-check:
	$(UV) run python manage.py check

migrations-check:
	$(UV) run python manage.py makemigrations --check --dry-run \
		--settings=notifications.settings.test

check: lint types django-check migrations-check test

up:
	$(COMPOSE) up --build --detach --wait

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs --follow web worker

migrate:
	$(COMPOSE) run --rm migrate

smoke:
	./scripts/smoke.sh
