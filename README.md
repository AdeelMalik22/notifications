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
make ci
make format
make test
make migrate
make logs
make down
```

`make down` preserves database and broker volumes. It does not delete developer
data.

Every push and pull request runs the same quality gates in GitHub Actions,
including coverage, migration consistency, OpenAPI validation, Django deployment
checks, a real PostgreSQL/Redis/RabbitMQ integration pass, and a production image
build.

`make ci` runs the host-side quality gates. GitHub additionally starts real
services and boots the production container image.

## Runtime responsibilities

- `web`: Django/DRF under Gunicorn.
- `migrate`: one-shot Django migration process.
- `worker`: Celery worker using RabbitMQ.
- `db`: PostgreSQL system of record.
- `redis`: Django cache and future atomic rate-limit counters.
- `mailpit`: local SMTP capture.

Celery task results are disabled. Delivery history will be stored in PostgreSQL,
and Redis must never become the source of truth for notification state.

## Tenant API keys

Tenant API keys are bearer credentials in the form
`nos_<prefix>.<secret>`. Only the prefix and a keyed digest are stored. The
secret is returned only when the key is created.

The tenancy management endpoints are available under `/api/v1/`:

- `GET /api/v1/api-keys/` lists keys for the authenticated tenant and requires
  `api_keys:read`.
- `POST /api/v1/api-keys/` creates a key and requires `api_keys:write`.
- `POST /api/v1/api-keys/{id}/rotate/` replaces a usable key and returns the
  replacement secret once.
- `POST /api/v1/api-keys/{id}/revoke/` revokes a key and requires
  `api_keys:write`.

Use the key with the standard bearer header:

```http
Authorization: Bearer nos_<prefix>.<secret>
```

For local development, create the initial tenant and key from the Django shell:

```bash
uv run python manage.py shell
```

```python
from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

business = create_business("Example business")
key, secret = create_api_key(
    business,
    "local development",
    [APIKey.Scope.API_KEYS_READ, APIKey.Scope.API_KEYS_WRITE,
     APIKey.Scope.NOTIFICATIONS_WRITE],
)
print(secret)
```

Never place the returned secret in source control or application logs.

## Catalogue and recipients

See the detailed [catalogue API reference](docs/api/catalogue.md).

The initial tenant-scoped management resources are available under `/api/v1/`:

- `GET/POST /categories/`
- `GET/POST /event-types/`
- `GET/POST /templates/`
- `GET/POST /template-versions/`
- `GET/POST /recipients/`
- `GET/POST /preferences/`

Template lifecycle actions are available at:

- `POST /api/v1/template-versions/{id}/publish/`
- `POST /api/v1/template-versions/{id}/preview/`

## Triggering notifications

Create an asynchronous notification with a required idempotency key:

```http
POST /api/v1/notifications/
Authorization: Bearer nos_<prefix>.<secret>
Idempotency-Key: order-shipped-123
Content-Type: application/json
```

```json
{
  "event_type": "order.shipped",
  "recipient_id": "<recipient-id>",
  "variables": {"customer_name": "Ada"}
}
```

The API returns `202 Accepted` after the notification, delivery snapshot, and
transactional outbox record commit. Repeating the same key and canonical
payload returns the original notification; reusing it with different data
returns `409 Conflict`.

Delivery history is available through:

- `GET /api/v1/notifications/history/`
- `GET /api/v1/notifications/{id}/`

The outbox relay publishes opaque delivery identifiers to Celery. Workers
reload snapshots from PostgreSQL, execute the configured local provider, and
record delivery attempts in PostgreSQL.

All records are associated with the authenticated API key's tenant; callers
cannot provide or override `business_id`. Categories support transactional,
marketing, and mandatory policies. Marketing preferences default to explicit
opt-in at evaluation time, while mandatory categories cannot be disabled.
Published template versions must declare exactly the variables defined by
their event type. Preview performs restricted variable substitution and never
sends a notification. Update/delete lifecycle actions and production provider
configuration remain planned work.
