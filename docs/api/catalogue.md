# Catalogue, recipients, and preferences API

All endpoints are under `/api/v1/` and require a tenant API key:

```http
Authorization: Bearer nos_<prefix>.<secret>
```

The tenant is derived from the authenticated key. `business_id` is never
accepted from request data, and every list query is scoped to that tenant.

## Categories

`GET /categories/` lists categories. `POST /categories/` creates one:

```json
{
  "key": "security",
  "name": "Security notifications",
  "policy": "mandatory"
}
```

Allowed policies are `transactional`, `marketing`, and `mandatory`. Category
keys are unique within a tenant.

## Event types

`GET /event-types/` lists event types. `POST /event-types/` creates one:

```json
{
  "key": "order.shipped",
  "name": "Order shipped",
  "category": "<category-id>",
  "variable_schema": ["customer_name", "tracking_url"]
}
```

The referenced category must belong to the authenticated tenant. Event keys
are unique within a tenant.

## Templates and versions

`GET /templates/` and `POST /templates/` manage channel-specific template
identities. Channels are `email` and `sms`:

```json
{
  "event_type": "<event-type-id>",
  "channel": "email"
}
```

`GET /template-versions/` and `POST /template-versions/` manage version
records. A draft becomes immutable when published:

```json
{
  "template": "<template-id>",
  "version": 1,
  "status": "published",
  "subject": "Your order shipped",
  "body": "Hello {{ customer_name }}",
  "variables": ["customer_name", "tracking_url"]
}
```

Published versions must declare exactly the variables in the event type's
schema. Use `POST /template-versions/{id}/publish/` to publish a draft and
`POST /template-versions/{id}/preview/` with a `variables` object to render a
synthetic preview. Preview never sends a notification.

## Recipients

`GET` and `POST /recipients/` list and create recipients. Detail endpoints also
support `GET`, `PATCH`, `PUT`, and `DELETE`:

```json
{
  "external_id": "user_123",
  "email": "user@example.test",
  "phone_number": "+15551234567"
}
```

`external_id` is unique within a tenant. Contact encryption and keyed lookup
hashes remain production-hardening work before external provider delivery.

## Preferences

`GET` and `POST /preferences/` list and create preferences. Detail endpoints
also support `GET`, `PATCH`, `PUT`, and `DELETE`:

```json
{
  "recipient": "<recipient-id>",
  "category": "<category-id>",
  "channel": "email",
  "enabled": true
}
```

Preferences are unique by tenant, recipient, category, and channel. Mandatory
categories cannot be disabled. Marketing categories require explicit opt-in;
transactional notifications are enabled by default unless explicitly
suppressed.

## Current scope

Catalogue and recipient lifecycle actions, template publishing/preview,
tenant-scoped audit records for sensitive key operations, and the notification
trigger endpoint are implemented. Provider configuration, contact protection,
and operational hardening remain production-readiness work.
