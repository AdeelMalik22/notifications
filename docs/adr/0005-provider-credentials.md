# ADR 0005: Provider credential encryption

- Status: accepted
- Decision: tenant-owned provider credentials will be encrypted before storage
  with a dedicated encryption key, separate from Django's `SECRET_KEY`. Key
  rotation and access auditing are required before provider configuration ships.
- Rationale: compromise of the database must not disclose provider secrets.

