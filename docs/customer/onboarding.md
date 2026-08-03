# Customer onboarding quickstart

This guide takes a new tenant from an API key to a verified notification.
Use HTTPS in every non-local environment.

## 1. Create a tenant key

An operator creates a business and API key using the approved provisioning
process. The API secret is displayed once. Store it in the customer's secret
manager and never in source control, tickets, or logs.

The sending key needs `notifications:write`. Separate catalogue and API-key
management scopes should be issued only when required.

## 2. Register catalogue data

Create a category, event type, channel template, and published template
version. Start with a transactional category and an email template. Declare
the variables used by the template; missing variables reject a trigger before
delivery.

## 3. Register a recipient

Create a recipient with the customer's stable `external_id` and contact
details. Contacts are encrypted at rest. Add explicit category/channel
preferences when the default policy is not appropriate. Marketing categories
require opt-in; mandatory categories cannot be disabled.

## 4. Send a test notification

```bash
curl -X POST https://api.example.test/api/v1/notifications/ \
  -H "Authorization: Bearer $NOTIFICATIONOS_API_KEY" \
  -H "Idempotency-Key: onboarding-$(date +%s)" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"order.shipped","recipient_id":"<recipient-uuid>","variables":{"name":"Ada"}}'
```

Expect `202 Accepted` and a `notification_id`. The API does not wait for the
provider. Query the notification history until the delivery is `sent`, or
inspect its attempts when it is `failed` or `unknown`.

## 5. Production checklist

- Use a dedicated API key per environment and rotate it during handoff.
- Configure provider credentials through the provider-management API; verify
  they are not present in responses or logs.
- Set alerting for delivery failures and confirm a synthetic notification.
- Confirm the customer's plan cap and provider spend limits.
- Document the customer's event names, escalation contact, and data-deletion
  request path.
- Explain that `sent` means provider acceptance, not handset delivery, opening,
  or reading.

## Limits and lifecycle

The current plans and support commitments are in
[`pricing-and-support.md`](pricing-and-support.md). Content is removed after
30 days and non-PII delivery metadata is retained for 90 days. Customers must
use the delivery history API for operational status; NotificationOS does not
provide a notification-center UI in this MVP.
