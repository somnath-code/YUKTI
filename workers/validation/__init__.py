import json
from adapters.postgres.store import Database
from packages.core.events import now
from packages.core.settings import policy
from packages.provenance.sources import canonical_url


def validate(db: Database, tenant: str) -> dict:
    limit = policy('quality')['evidence_review_limit']
    errors = []
    with db.transaction(tenant, write=True) as tx:
        rows = tx.all(
            'SELECT urn,source_url,metadata FROM evidence WHERE tenant=%s ORDER BY collected_at DESC,urn LIMIT %s',
            (tenant, limit))
        for row in rows:
            try:
                canonical_url(row['source_url'])
                metadata = json.loads(row['metadata'])
                if policy('critical')['reject_empty_title'] and not str(metadata.get('title') or '').strip():
                    raise ValueError('Missing title')
                if metadata.get('topic') not in policy('contracts')['topics']:
                    raise ValueError('Unexpected topic')
                if metadata.get('kind') not in policy('contracts')['publication_types']:
                    raise ValueError('Unexpected publication type')
            except (ValueError, TypeError, AttributeError) as exc:
                errors.append({'urn': row['urn'], 'error': str(exc)})
                if policy('critical')['quarantine_invalid_evidence']:
                    tx.run("""INSERT INTO evidence_quarantine VALUES (%s,%s,%s,%s,%s)
                        ON CONFLICT (tenant,urn) DO UPDATE SET reason=excluded.reason""",
                        (tenant, row['urn'], str(exc), now(), row['source_url']))
            else:
                tx.run('DELETE FROM evidence_quarantine WHERE tenant=%s AND urn=%s', (tenant,row['urn']))
    return {'checked': len(rows), 'errors': errors}
