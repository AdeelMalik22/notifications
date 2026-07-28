# ADR 0005: Provider credential encryption

- Status: accepted
- Decision: tenant-owned provider credentials are encrypted before storage with
  Fernet and a dedicated `PROVIDER_ENCRYPTION_KEY`, separate from Django's
  `SECRET_KEY`. The key is supplied through the environment and is never stored
  in PostgreSQL or returned by the API.
- Rationale: compromise of the database must not disclose provider secrets.
- Implementation: `ProviderConfiguration` stores ciphertext only; the delivery
  service decrypts credentials just before provider construction. Key rotation
  and provider access auditing remain production-hardening work.
