from adapters.ollama.client import Ollama
from adapters.postgres.store import Database
from adapters.vector_store.sql import save
from packages.contracts.models import Brief


def index(db: Database, tenant: str, model: Ollama, limit: int = 30) -> dict:
    with db.transaction(tenant) as tx:
        rows = tx.all("""SELECT a.id,a.revision,a.payload FROM articles a LEFT JOIN vectors v
            ON a.tenant=v.tenant AND a.id=v.article_id AND v.model=%s AND a.revision=v.revision
            WHERE a.tenant=%s AND a.state='reviewed' AND v.article_id IS NULL
            ORDER BY a.id LIMIT %s""", (model.embedding_model, tenant, limit))
    for row in rows:
        brief = Brief.model_validate_json(row['payload'])
        values = model.embed(f'{brief.title} {brief.summary}')
        with db.transaction(tenant, write=True) as tx:
            save(tx, tenant, row['id'], row['revision'], model.embedding_model, values)
    return {'indexed': len(rows)}
