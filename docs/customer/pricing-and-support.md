# Pricing, support, and service policy

These are the pilot-release commercial defaults. Provider fees, taxes, and
optional implementation work are billed separately.

## Plans

| Plan | Monthly platform fee | Included notifications/month | Recipient cap | Support |
|---|---:|---:|---:|---|
| Free | $0 | 1,000 | 1,000 | Documentation and community support |
| Professional | $49 | 100,000 | 100,000 | Email support, one-business-day response |
| Enterprise | From $499 | 1,000,000 | 1,000,000 | Named support contact, priority escalation |

Professional and Enterprise customers bring their own provider credentials;
email/SMS provider charges are not included. Usage above a plan cap is
rejected with `429` until the plan is upgraded or the next billing month
starts. Rate limits, payload limits, and the 1,000-item default unpublished
outbox safety cap apply independently of monthly volume.

Enterprise pricing may be adjusted for negotiated volume, retention, support,
or deployment requirements. SSO, private deployments, formal SLAs, and
enterprise audit exports are not part of this MVP and require a separate
contract and product approval.

## Support process

Customers open a support request through the configured support mailbox or
account channel. Every request should include:

- business public ID, environment, and approximate UTC time;
- request ID or notification/delivery ID;
- endpoint and HTTP status, excluding API keys and message content;
- impact, affected channel, and whether delivery is time-sensitive.

Never send API secrets, provider credentials, recipient contacts, rendered
messages, or raw payloads in a support ticket. Support may request redacted
logs or IDs only.

Severity targets:

| Severity | Definition | Initial response |
|---|---|---:|
| P1 | Broad outage, data-loss risk, or suspected cross-tenant exposure | 1 hour |
| P2 | Major delivery degradation or provider outage for one or more tenants | 4 business hours |
| P3 | Individual failed deliveries, configuration, or API questions | 1 business day |
| P4 | Documentation, feature request, or billing question | 3 business days |

P1/P2 incidents receive an incident owner, status updates at least every two
hours, and a written summary after recovery. Security reports are escalated
immediately to the security owner and handled outside the normal queue.
