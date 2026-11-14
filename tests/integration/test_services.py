from dataclasses import replace
from pathlib import Path
import os
import time
from uuid import uuid4
import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from adapters.identity_provider.tokens import TokenVerifier
from adapters.grammar_checker.client import LanguageTool
from adapters.ollama.client import Ollama
from adapters.pyspark.bulk import run
from packages.core.settings import ROOT, Settings


@pytest.mark.live
def test_real_postgres_rls(runtime):
    if not runtime.db.pg:
        pytest.skip('YUKTI_TEST_DATABASE is unset')
    runtime.db.migrate()
    from workers.ingestion import collect
    tenant = 'test-' + uuid4().hex[:8]
    collect(runtime.db,runtime.artifacts,tenant,live=False)
    with runtime.db.transaction(tenant) as tx:
        assert tx.one('SELECT count(*) AS n FROM evidence')['n'] == 2
    with runtime.db.transaction('different-tenant') as tx:
        assert tx.one('SELECT count(*) AS n FROM evidence')['n'] == 0


@pytest.mark.live
def test_real_ollama():
    url = os.getenv('YUKTI_TEST_OLLAMA')
    if not url:
        pytest.skip('YUKTI_TEST_OLLAMA is unset')
    model = Ollama(url,'qwen2.5:0.5b')
    assert model.suggest('The YUKTI test run started on a Sunday.')
    assert len(model.embed('Automatic differentiation')) > 32


@pytest.mark.spark
def test_spark_actual_parquet(tmp_path):
    if os.getenv('YUKTI_TEST_SPARK') != '1':
        pytest.skip('Set YUKTI_TEST_SPARK=1 and run uv sync --locked --group spark and install Java')
    assert run(ROOT / 'data/samples/analytics.jsonl',tmp_path / 'output') == 3
    assert list((tmp_path/'output').glob('*.parquet'))
