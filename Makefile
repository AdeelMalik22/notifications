UV := uv
COMPOSE := docker compose

.PHONY: install format lint types test coverage django-check migrations-check \
	schema-check production-check compose-check check ci up down logs migrate smoke

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

coverage:
	$(UV) run pytest --cov=apps --cov=notifications --cov-report=term-missing \
		--cov-report=xml --cov-fail-under=85

django-check:
	$(UV) run python manage.py check

migrations-check:
	$(UV) run python manage.py makemigrations --check --dry-run \
		--settings=notifications.settings.test

schema-check:
	$(UV) run python manage.py spectacular --validate --file /tmp/notificationos-schema.yml \
		--settings=notifications.settings.test

production-check:
	DJANGO_SETTINGS_MODULE=notifications.settings.production \
	DJANGO_SECRET_KEY=production-check-only-7gVQ2mZ9xK4pR8sT1wY6nC3dF5hJ0-not-for-deployment \
	DJANGO_ALLOWED_HOSTS=notifications.example.test \
	$(UV) run python manage.py check --deploy --fail-level WARNING

compose-check:
	$(COMPOSE) config --quiet

check: lint types django-check migrations-check schema-check compose-check test

ci: lint types django-check migrations-check schema-check production-check compose-check coverage

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
