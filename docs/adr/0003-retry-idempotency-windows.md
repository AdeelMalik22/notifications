# ADR 0003: Retry and idempotency windows

- Status: accepted
- Decision: delivery has three total attempts, with 60 seconds between retries.
  Active idempotency keys are retained for 30 days; non-PII tombstones remain
  for 90 days.
- Rationale: bound duplicate risk and storage while covering normal client
  retry behavior.

