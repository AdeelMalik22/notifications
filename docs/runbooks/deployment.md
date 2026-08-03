# Production deployment and rollback

NotificationOS is deployed as one immutable application release. The web
process, migration job, and Celery worker must use the same image digest.
PostgreSQL is the source of truth; Redis and RabbitMQ are managed dependencies.
TLS termination, secret storage, backups, monitoring, and alerting belong at
the hosting platform or private network boundary.

## Backup, RPO, and RTO policy

The production target is:

- **RPO: 15 minutes.** At most 15 minutes of committed PostgreSQL state may be
  lost. Use continuous WAL archiving or the managed PostgreSQL provider's
  point-in-time recovery (PITR). A nightly `pg_dump` alone does not satisfy
  this target.
- **RTO: 60 minutes.** The API and workers must be restored and accepting
  verified synthetic traffic within 60 minutes of declaring a database or
  application outage.

The minimum schedule is:

- Continuous WAL/PITR enabled and monitored.
- One encrypted PostgreSQL custom-format full backup every 24 hours, retained
  for 35 days.
- One monthly full backup retained for 12 months.
- A restore drill once per month, using the newest daily backup and a separate
  isolated database or temporary managed instance.
- A quarterly PITR drill that restores to a timestamp within the last 15 days.

Backups must be encrypted at rest and in transit, stored outside the primary
database host/volume, access-controlled, and monitored for age and failure.
The on-call owner records backup timestamp, WAL/PITR health, restore duration,
verification result, and any corrective action. Alert if the newest successful
backup is older than 26 hours, WAL/PITR lag exceeds 15 minutes, or a restore
drill fails.

Redis rate-limit counters and RabbitMQ transient queue state are not backed up
as system-of-record data. After a disaster, accepted notifications and
delivery state come from PostgreSQL; reconciliation must inspect unpublished
outbox rows and ambiguous deliveries before replaying work.

## Restore verification drill

Never restore over the primary during a drill. Provision an empty isolated
PostgreSQL database with the same major version and run:

```bash
./scripts/verify_postgres_backup.sh \
  /secure/notifications-backups/notifications-<timestamp>.dump \
  postgresql://restore_user:password@restore-host:5432/notifications_restore
```

The script must complete with `recovery verification passed`. Then verify the
restored database has the migration table and core tables, run Django checks
against the restored connection, and perform a read-only API smoke test. A
successful drill requires all of the following:

- restore exits successfully without manual SQL fixes;
- `django_migrations` is present and migrations are complete;
- `tenancy_business`, `notifications_notification`, `notifications_delivery`,
  and `notifications_outboxevent` exist;
- row counts for a selected known tenant and recent notification are present;
- `manage.py check --deploy` passes with production settings;
- restore duration is recorded and is below the 60-minute RTO.

Destroy the isolated database after recording the result. A failed drill is a
production incident for backup reliability: open a corrective action, rerun
the drill, and do not mark the backup policy verified until it passes.

## Required production configuration

Set these values in the platform secret/configuration store, not in Git:

- `NOTIFICATIONOS_IMAGE`: immutable registry tag or digest.
- `NOTIFICATIONOS_ENV_FILE`: mounted environment file containing production
  `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, database credentials, Redis and
  RabbitMQ URLs, `PROVIDER_ENCRYPTION_KEY`, `CONTACT_ENCRYPTION_KEY`, and
  `CONTACT_LOOKUP_KEY`.
- `DJANGO_SETTINGS_MODULE=notifications.settings.production`.
- `DJANGO_CSRF_TRUSTED_ORIGINS` for the HTTPS public origin.
- `DEFAULT_FROM_EMAIL` and real provider configuration.
- Numerical admission limits from `.env.example`, reviewed against the plan.

The production image is built by the CI workflow. Promote only an image whose
formatting, lint, type, test, migration, schema, deployment-check, and image
checks passed. Use `compose.production.yaml` as the reference process layout;
the same web, migrate, and worker commands may be translated to the hosting
platform's job/service model.

## Release procedure

1. Confirm the image digest and CI result. Confirm a recent backup and that no
   restore drill or provider incident is active.
2. Run the production deployment check and validate the image locally or in a
   staging environment:

   ```bash
   docker run --rm --env-file "$NOTIFICATIONOS_ENV_FILE" \
     -e DJANGO_SETTINGS_MODULE=notifications.settings.production \
     "$NOTIFICATIONOS_IMAGE" python manage.py check --deploy --fail-level WARNING
   ```

3. Start the migration job from the new image. Migrations must be additive and
   backward-compatible with the currently running release.
4. Roll out web instances gradually. Wait for `/health/ready` on each new
   instance before routing traffic to it.
5. Roll out workers using the same image. Keep the previous worker image
   available until queued tasks from the old contract are drained.
6. Verify liveness, readiness, error rate, queue age, unpublished outbox age,
   dead letters, and a synthetic trigger-to-provider delivery.
7. Record image digest, migration names, deployment time, operator, and
   verification results in the release log.

## Rollback procedure

Rollback is appropriate for elevated 5xx responses, failed readiness, broken
delivery, unsafe latency, or a migration/application incompatibility.

1. Stop promotion and preserve logs, metrics, request IDs, and the failing
   image digest. Do not delete the database, queues, or volumes.
2. If the migration job failed before applying changes, redeploy the previous
   image and stop there.
3. If migrations succeeded, first determine whether they are backward
   compatible. Deploy the previous image only when its code can read the
   migrated schema. Never run `migrate --fake` or manually delete migration
   rows to force a rollback.
4. Route traffic to healthy previous-image web instances, then replace workers
   with the previous image. Keep the new image available for investigation.
5. Check `/health/ready`, API 5xx rate, queue age, outbox age, worker health,
   and delivery attempts. Send one synthetic notification and verify its
   history.
6. If the schema is not backward compatible, keep the compatible application
   release deployed and prepare a forward-fix release. Restore the database
   only for confirmed data corruption, using the backup restore runbook and an
   approved maintenance window.
7. Reconcile ambiguous deliveries before replaying work. Provider calls can
   have unknown outcomes; never blindly replay all queued messages.
8. Document the incident, affected migrations, customer impact, and the
   forward-fix or recovery decision.

## Rollback safety rules

- Backward-compatible expand/contract migrations are required for zero-downtime
  releases: add nullable/schema-compatible fields first, deploy code, backfill,
  then remove old fields in a later release.
- Do not change Celery task argument contracts in place. Keep old workers able
  to consume queued messages during a rolling deployment.
- Secrets and encryption keys must remain stable across a rollback.
- Database restore is a last resort and requires isolated verification first;
  use `scripts/verify_postgres_backup.sh` before touching the primary.
- Rollback does not revoke API keys or erase notification history.
