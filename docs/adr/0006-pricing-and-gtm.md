# ADR 0006: Pilot pricing and go-to-market

- Status: accepted
- Date: 2026-08-03

## Decision

Launch with three plans aligned to the enforced tenant caps:

| Plan | Monthly fee | Notifications/month | Recipients |
|---|---:|---:|---:|
| Free | $0 | 1,000 | 1,000 |
| Professional | $49 | 100,000 | 100,000 |
| Enterprise | From $499 | 1,000,000 | 1,000,000 |

Provider charges are excluded. Professional support is email-based with a
one-business-day initial response target. Enterprise includes a named support
contact and priority escalation. Formal SLAs, SSO, private deployments, and
enterprise audit exports remain separately contracted future scope.

The first go-to-market motion is a developer-led pilot: documentation and a
working quickstart, a small number of SaaS design partners, and customer-owned
provider credentials. The onboarding and support commitments are defined in
`docs/customer/`.

Usage above the monthly plan cap is rejected with `429`; upgrades are handled
operationally until billing automation is introduced. Pricing may be reviewed
after the first 10 pilot customers, but changes require an ADR and a matching
update to configured plan limits and customer documentation.
