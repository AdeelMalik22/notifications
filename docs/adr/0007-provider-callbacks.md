# ADR 0007: Provider callback boundary

- Status: accepted
- Date: 2026-08-03

## Decision

Provider delivery/bounce callbacks are deferred for the MVP and public pilot.
The authoritative status remains provider acceptance recorded by the worker:
`sent` does not mean delivered to a handset, opened, or read. Ambiguous worker
outcomes remain `unknown` and are handled through provider-specific
reconciliation rather than blind retry.

Callbacks will be reconsidered when a pilot customer requires bounce, delivery,
or opt-out synchronization. Before enabling them, the implementation must add:

- signed webhook endpoints under `/api/v1/` with replay protection;
- provider-specific event normalization and idempotent event storage;
- tenant-scoped event correlation without exposing provider secrets or PII;
- customer documentation for status semantics and retention;
- tests for invalid signatures, duplicate events, out-of-order events, and
  cross-tenant event IDs.

Until then, customers should use delivery history and provider dashboards for
operational investigation. This decision does not prevent the existing
reconciliation tooling for ambiguous outcomes.
