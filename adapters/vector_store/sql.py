import json
import math
from packages.core.events import encoded
from packages.core.settings import policy


def save(tx, tenant: str, article_id: str, revision: int, model: str, values: list[float]) -> None:
    tx.run("""INSERT INTO vectors VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (tenant,article_id,model) DO UPDATE SET revision=excluded.revision,
          dimensions=excluded.dimensions,values_json=excluded.values_json
        WHERE vectors.revision <= excluded.revision""",
        (tenant, article_id, revision, model, len(values), encoded(values)))


def nearest(tx, tenant: str, model: str, query: list[float], limit: int = 10) -> list[dict]:
    rows = tx.all("""SELECT a.id,a.payload,v.values_json FROM vectors v JOIN articles a
            ON a.tenant=v.tenant AND a.id=v.article_id AND a.revision=v.revision
            WHERE v.tenant=%s AND v.model=%s AND v.dimensions=%s AND a.state='reviewed'
            ORDER BY a.id LIMIT %s""", (tenant, model, len(query), policy('ranking')['vector_candidate_limit']))
    norm = math.sqrt(sum(x * x for x in query))
    ranked = []
    for row in rows:
        vector = json.loads(row['values_json'])
        denom = norm * math.sqrt(sum(x * x for x in vector))
        if denom:
            similarity = sum(a * b for a, b in zip(vector, query, strict=True)) / denom
            ranked.append({'id': row['id'], 'article': json.loads(row['payload']), 'score': similarity})
    return sorted(ranked, key=lambda row: -row['score'])[:limit]
