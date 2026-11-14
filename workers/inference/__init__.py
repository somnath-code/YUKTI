import json
from adapters.ollama.client import Ollama
from adapters.postgres.store import Database
from packages.editorial.service import Problem
from packages.intelligence.suggestions import propose


def suggest(db: Database, tenant: str, urn: str, model: Ollama) -> dict:
    with db.transaction(tenant) as tx:
        row = tx.one('''SELECT e.metadata,e.source_url FROM evidence e WHERE e.tenant=%s AND e.urn=%s
              AND NOT EXISTS (SELECT 1 FROM evidence_quarantine q WHERE q.tenant=e.tenant AND q.urn=e.urn)''', (tenant, urn))
    if row is None:
        raise Problem(404, 'Evidence not found')
    evidence = json.loads(row['metadata'])
    return {**propose(model, evidence['title'] + '\n' + evidence['raw_text']), 'source_url': row['source_url']}
