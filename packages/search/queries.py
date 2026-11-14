from adapters.postgres.store import Tx


def search(tx: Tx, tenant: str, query: str, topic: str | None, kind: str | None, limit: int) -> list[dict]:
    sql = 'SELECT id,payload,revision FROM articles WHERE tenant=%s AND state=%s'
    args: list = [tenant, 'reviewed']
    if tx.pg and query:
        sql += """ AND to_tsvector('english', ((payload::jsonb)->>'title') || ' ' ||
            ((payload::jsonb)->>'summary') || ' ' || (((payload::jsonb)->'source')->>'venue'))
            @@ plainto_tsquery('english', %s)"""
        args.append(query)
    elif query:
        sql += " AND instr(lower(json_extract(payload,'$.title') || ' ' || json_extract(payload,'$.summary') || ' ' || json_extract(payload,'$.source.venue')), lower(%s)) > 0"
        args.append(query)
    for key, value in [('topic', topic), ('kind', kind)]:
        if value:
            sql += f" AND (payload::jsonb)->>'{key}'=%s" if tx.pg else f" AND json_extract(payload,'$.{key}')=%s"
            args.append(value)
    return tx.all(sql + ' ORDER BY id LIMIT %s', (*args, limit))
