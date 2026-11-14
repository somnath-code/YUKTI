# Operational schemas

Migrations are canonical. Articles store a typed brief snapshot as JSON text for portability. PostgreSQL uses JSONB expressions to build a GIN text index and filter kind and topic. A tenant and article ID form the key. A tenant and canonical URL form a second unique key. Editing a brief invalidates its previous review and increments the revision.

Issues store the ordered article snapshots, including their revision, and the digest of the rendered PDF. A tenant and issue ID form the key. The weekly job uses a deterministic date-based ID. Evidence stores file digests and the exact parsed metadata. Audit entries and release outbox rows commit with the corresponding state transition. Vectors bind to the article revision and embedding model. The analytics fixture projects only tenant, topic, kind and URL into Parquet aggregates.

Migration 004 adds one quarantine record per tenant and evidence ID. PostgreSQL migration 005 forces row-level security on this table. The validator removes the quarantine marker after a record passes its next validation.
