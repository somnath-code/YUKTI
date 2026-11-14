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
from tests.end_to_end.test_editorial import TestVerifier, auth


def test_concurrent_duplicate_only_one_commits(runtime, catalog):
    tenant = 'race-' + uuid4().hex[:8]
    with TestClient(create_app(runtime.settings, runtime=runtime, verifier=TestVerifier(tenant))) as client:
        def write(_):
            return client.post('/api/articles', json=catalog['articles'][0], headers=auth('curator')).status_code
        with ThreadPoolExecutor(max_workers=6) as pool:
            assert sorted(pool.map(write, range(6))) == [201,409,409,409,409,409]
