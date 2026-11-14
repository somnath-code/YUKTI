from packages.core.events import encoded, now


def enqueue(tx, tenant: str, event_id: str, kind: str, payload: dict) -> None:
    tx.run(
        'INSERT INTO outbox(tenant,id,kind,payload,created_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
        (tenant, event_id, kind, encoded(payload), now()),
    )
