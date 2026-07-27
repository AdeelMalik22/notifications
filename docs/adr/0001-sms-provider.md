# ADR 0001: Use a Twilio-compatible SMS provider interface

- Status: accepted
- Decision: production SMS uses a Twilio-compatible adapter; local development
  uses the deterministic fake adapter.
- Rationale: this keeps the delivery contract stable while allowing local tests
  without external calls. Provider failover is deferred.

