# ADR 0004: Notification data retention

- Status: accepted
- Decision: encrypted payload and rendered content are erased after 30 days;
  non-PII delivery metadata is retained for 90 days. Deletion jobs anonymize
  recipient data while preserving permitted operational records.

