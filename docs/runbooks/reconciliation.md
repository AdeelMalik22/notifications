# Reconciliation, alerting, and dead-letter replay

## Alerts

Load [`docs/monitoring/alerts.yml`](../monitoring/alerts.yml) into the
Prometheus-compatible monitoring system and provide the delivery/outbox gauges
from the database metrics collector. Keep `/health/metrics` private. Page on
readiness failures and unknown provider outcomes; notify the delivery operator
for dead letters and an aging outbox.

## Reconcile provider outcomes

An `unknown` delivery means the provider outcome could not be inferred safely.
It must not be blindly retried. Run:

```bash
python manage.py reconcile_deliveries
```

The command is read-only. The provider-specific reconciliation worker should
query the provider using its stable message/idempotency key, then transition
the delivery to `sent` or `failed` and record an attempt. Until that adapter is
available, escalate the listed delivery IDs to the provider/operator and keep
them visible as `unknown`.

## Replay dead letters

Dead-letter replay is explicit and idempotent. First inspect the candidates:

```bash
python manage.py reconcile_deliveries
python manage.py replay_dead_letters <delivery-uuid>
```

Review the provider error, recipient, template version, and current incident
before confirming:

```bash
python manage.py replay_dead_letters --confirm <delivery-uuid>
```

The command only accepts deliveries with `dead_lettered_at`, resets them to
`pending`, unpublishes their existing outbox row, and lets the normal relay
publish them. It refuses missing, sent, unknown, or non-dead-lettered IDs.
Do not replay a delivery when the provider may already have accepted it;
reconcile that outcome first.

After replay, verify a new delivery attempt, final status, outbox age, and
provider response. Record the operator, IDs, reason, and result in the
incident log.
