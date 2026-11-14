from uuid import uuid4
from workers.ingestion import collect
from workers.validation import validate


def test_invalid_evidence_is_quarantined_once_and_recoverable(runtime):
    runtime.db.migrate()
    tenant = 'quarantine-' + uuid4().hex[:8]
    assert set(collect(runtime.db, runtime.artifacts, tenant, live=False, group='news')['feeds']) == {'postgresql-news'}
    with runtime.db.transaction(tenant, write=True) as tx:
        original = tx.one('SELECT urn,metadata FROM evidence WHERE tenant=%s', (tenant,))
        tx.run('UPDATE evidence SET metadata=%s WHERE tenant=%s AND urn=%s', ('{}',tenant,original['urn']))
    assert validate(runtime.db, tenant)['errors'][0]['urn'] == original['urn']
    validate(runtime.db, tenant)
    with runtime.db.transaction(tenant, write=True) as tx:
        assert tx.one('SELECT count(*) AS n FROM evidence_quarantine WHERE tenant=%s', (tenant,))['n'] == 1
        tx.run('UPDATE evidence SET metadata=%s WHERE tenant=%s AND urn=%s',(original['metadata'],tenant,original['urn']))
    assert not validate(runtime.db, tenant)['errors']
    with runtime.db.transaction(tenant) as tx:
        assert tx.one('SELECT count(*) AS n FROM evidence_quarantine WHERE tenant=%s', (tenant,))['n'] == 0
