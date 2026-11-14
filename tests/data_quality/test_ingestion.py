from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4
from fastapi.testclient import TestClient
from pypdf import PdfReader
from apps.api.main import create_app
from packages.identity.access import Principal
from workers.ingestion import collect
from workers.layout_validation import check as check_layout
from workers.validation import validate


def test_ingestion_and_retry(runtime):
    runtime.db.migrate()
    tenant = 'ingest-' + uuid4().hex[:8]
    first = collect(runtime.db, runtime.artifacts, tenant, live=False)
    again = collect(runtime.db, runtime.artifacts, tenant, live=False)
    assert sum(x['new'] for x in first['feeds'].values()) == 2
    assert sum(x['new'] for x in again['feeds'].values()) == 0
    assert validate(runtime.db, tenant) == {'checked':2,'errors':[]}
    assert validate(runtime.db, 'isolated-demo')['checked'] == 0
