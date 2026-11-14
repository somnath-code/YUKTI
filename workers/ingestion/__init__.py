from adapters.postgres.store import Database
from packages.contracts.models import ArtifactStore
from packages.core.events import encoded, now
from packages.core.settings import policy
from packages.ingestion.feeds import parse, snapshot
from packages.provenance.sources import digest


def collect(db: Database, artifacts: ArtifactStore, tenant: str, *, live: bool, group: str | None = None) -> dict:
    counts, errors = {}, {}
    configured = policy('sources')['feeds']
    feeds = [cfg for cfg in configured if group is None or cfg['group'] == group]
    if not feeds:
        raise ValueError('Unknown source collection group')
    for cfg in feeds:
        feed_id = cfg['id']
        try:
            feed, content = snapshot(feed_id, live)
            records = parse(content, feed)
        except (ValueError, SyntaxError) as exc:
            errors[feed_id] = str(exc)
            continue
        checksum = artifacts.put(content)
        new = 0
        with db.transaction(tenant, write=True) as tx:
            for item in records:
                urn = digest(encoded([item.url, checksum, live]).encode())
                metadata = {**item.as_record(), 'feed_id': feed_id, 'fixture': not live}
                row = tx.one("""INSERT INTO evidence VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING RETURNING urn""",
                    (tenant, urn, item.url, checksum, encoded(metadata), now()))
                new += int(row is not None)
        counts[feed_id] = {'parsed': len(records), 'new': new}
    return {'feeds': counts, 'errors': errors}
