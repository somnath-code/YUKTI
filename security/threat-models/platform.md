# Threat model and security operations

| Trust boundary | Failure scenario | Local controls |
| --- | --- | --- |
| Source internet to ingestion | Host spoofing, redirects, XML expansion, oversize response | Exact allowlist, HTTPS, redirects disabled, defusedxml and bounded bytes |
| Browser to API | Forged token, leaked draft, unauthorised edit | RS256, JWKS, issuer and audience validation, expiration, roles, tenant claims, no-cache API, CSP |
| API to database | Cross-tenant query or duplicate write | Bound SQL parameters, tenant queries, PostgreSQL FORCE RLS and non-BYPASSRLS role, constraints |
| Editorial state and PDF | Self-approval, stale bytes, concurrent release | Independent subjects, compare-and-swap, content checksum, atomic audit/outbox transaction |
| AI and output | Misleading source text or output injection | Provenance retained, AI returned as a suggestion, escaping and asset-only PDF renderer |
| Local host | Credential exposure, stolen volume, admin misuse | Generated secrets, loopback publishing, minimal user roles, host backup access controls |

RBAC checks the action against the realm roles. ABAC checks the token's tenant and the issue's actor attributes. The database uses a transaction-local tenant setting. That setting protects accidental cross-tenant SQL. A compromised application process can choose a tenant, so its credentials remain a sensitive boundary. SQLite relies on app filtering. Do not reuse the local Keycloak development identity service, shared artifact volume or Compose environment secrets for production. Use TLS, an approved secret manager, separate DB owners and short-lived credentials. Keep access to containers and mounted data tightly controlled.

If compromise is suspected, preserve logs and snapshots, revoke affected sessions, rotate secrets and keys, block affected public connectors, check who approved and released issues, and compare stored checksums. Recover into an isolated environment, verify a sample of audit and PDF records, then reopen access. Local SQL audit is append-by-code. Production needs a write-only sink with restricted retention and independent integrity checks.
