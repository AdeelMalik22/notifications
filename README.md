# NotificationOS

NotificationOS is a Django and Django REST Framework notification platform. The
MVP is a modular monolith: the web process and Celery workers use the same
codebase, PostgreSQL database, and release.

## Repository layout

The repository is intentionally flat:

```text
.
├── manage.py
├── notifications/   # Django project package
├── apps/             # bounded domain applications
├── tests/
└── compose.yaml
```

There is no additional Django wrapper directory.

## Requirements

- Docker with Compose v2
- `uv` for host-based development
- Python 3.12 when running outside Docker

## Start the local stack

```bash
cp .env.example .env
make up
make smoke
```

Local endpoints:

- API documentation: <http://localhost:8000/api/docs/>
- OpenAPI schema: <http://localhost:8000/api/schema/>
- Liveness: <http://localhost:8000/health/live>
- Readiness: <http://localhost:8000/health/ready>
- Mailpit: <http://localhost:8025/>
- RabbitMQ management: <http://localhost:15672/>

The credentials in `.env.example` are deliberately local-only. Never reuse them
outside a developer machine.

## Development commands

```bash
make install
make check
make format
make test
make migrate
make logs
make down
```

`make down` preserves database and broker volumes. It does not delete developer
data.

## Runtime responsibilities

- `web`: Django/DRF under Gunicorn.
- `migrate`: one-shot Django migration process.
- `worker`: Celery worker using RabbitMQ.
- `db`: PostgreSQL system of record.
- `redis`: Django cache and future atomic rate-limit counters.
- `mailpit`: local SMTP capture.

Celery task results are disabled. Delivery history will be stored in PostgreSQL,
and Redis must never become the source of truth for notification state.
