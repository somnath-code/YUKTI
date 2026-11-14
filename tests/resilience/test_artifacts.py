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


def test_artifact_tampering(runtime):
    artifact = runtime.artifacts
    digest = artifact.put(b'exact sample')
    assert artifact.put(b'exact sample') == digest
    artifact.path(digest).write_bytes(b'tampered')
    import pytest
    with pytest.raises(OSError):
        artifact.get(digest)
