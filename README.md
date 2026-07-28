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
- Metrics: <http://localhost:8000/health/metrics> (protect this endpoint at the network layer)
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

The test suite includes unit tests for policies, serializers, providers, and
tasks; API contract tests for authentication, CRUD, idempotency, and tenant
scoping; Admin registration safety tests; and integration tests covering
tenant-isolated history plus the trigger-to-outbox-to-worker delivery path.
Run the full local suite with:

```bash
uv run pytest --cov=apps --cov=notifications --cov-fail-under=85
```

GitHub Actions additionally validates migrations against PostgreSQL, readiness
against PostgreSQL and Redis, OpenAPI generation, and a live Celery task through
RabbitMQ. The production-like broker/database checks complement the fast local
SQLite test suite.

## Operations and recovery

Every request carries an `X-Request-ID`, and structured JSON logs include that
ID and bounded request timing. The `/health/metrics` endpoint exposes process
counters in Prometheus format; scrape it only from a private monitoring
network. Alert on readiness failures, sustained HTTP 5xx responses, delivery
dead letters, and queue backlog.

Create a PostgreSQL custom-format backup with:

```bash
BACKUP_DIR=/secure/notifications-backups ./scripts/backup_postgres.sh
```

Recovery must be tested against an isolated PostgreSQL database, never the
primary database. Restore and verify a backup with:

```bash
./scripts/verify_postgres_backup.sh /secure/notifications-backups/notifications-<timestamp>.dump \
  postgresql://restore_user:password@localhost:5432/notifications_restore
```

Run backups on a schedule, encrypt them at rest, restrict access, retain them
according to the data-retention policy, and record the last successful backup
and recovery drill in the operations log.

When running Django directly with `notifications.settings.local`, the project
loads `.env` automatically. Production and test settings do not load `.env`.

## Runtime responsibilities

- `web`: Django/DRF under Gunicorn.
- `migrate`: one-shot Django migration process.
- `worker`: Celery worker using RabbitMQ.
- `db`: PostgreSQL system of record.
- `redis`: Django cache and atomic tenant/recipient rate-limit counters.
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

## Django Admin

The internal Admin site at `/admin/` registers every NotificationOS domain
model: tenants and API keys, catalogue and template versions, recipients and
preferences, provider configurations, notifications and delivery attempts,
outbox events, and audit events. Delivery snapshots, notification payloads,
provider ciphertext, API-key digests, and audit records are read-only to avoid
accidental mutation of operational history or secrets.

The initial tenant-scoped management resources are available under `/api/v1/`:

- `GET/POST /categories/`
- `GET/POST /event-types/`
- `GET/POST /templates/`
- `GET/POST /template-versions/`
- `GET/POST /recipients/`
- `GET/POST /preferences/`

Recipients and preferences also support tenant-scoped `GET`, `PATCH`, `PUT`,
and `DELETE` detail actions. Categories, event types, and template identities
support the same lifecycle endpoints.

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
reload snapshots from PostgreSQL, execute the configured provider, and record
delivery attempts in PostgreSQL. Local email uses Mailpit and local SMS uses
the deterministic fake provider. Production SMS uses the Twilio-compatible
adapter.

Provider credentials are encrypted at rest with `PROVIDER_ENCRYPTION_KEY`.
The key must be supplied through the environment before saving provider
configuration; it must never be committed or logged. Notification admission
limits are configured with `NOTIFICATION_TENANT_RATE_LIMIT` and
`NOTIFICATION_RECIPIENT_RATE_LIMIT`.

Recipient email addresses and phone numbers are encrypted at rest with the
separate `CONTACT_ENCRYPTION_KEY`. Normalized keyed HMAC digests using
`CONTACT_LOOKUP_KEY` support exact-match lookup without storing searchable
plaintext contact data. Keep both keys outside PostgreSQL and rotate them with
a controlled decrypt-and-reencrypt migration; losing either key makes the
corresponding contact data unrecoverable.

All records are associated with the authenticated API key's tenant; callers
cannot provide or override `business_id`. Categories support transactional,
marketing, and mandatory policies. Marketing preferences default to explicit
opt-in at evaluation time, while mandatory categories cannot be disabled.
Published template versions must declare exactly the variables defined by
their event type. Preview performs restricted variable substitution and never
sends a notification. Update/delete lifecycle actions and production provider
configuration remains subject to production deployment setup.
