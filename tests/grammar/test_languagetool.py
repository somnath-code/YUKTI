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


def test_grammar_contract_and_service_failure(monkeypatch):
    match = {'message':'Possible spelling mistake','offset':0,'length':4,'rule':{'id':'TEST','issueType':'misspelling'},'replacements':[{'value':'word'}]}
    monkeypatch.setattr(httpx,'post',lambda *a, **kw:httpx.Response(200,json={'matches':[match]},request=httpx.Request('POST','http://localhost')))
    client = LanguageTool('http://localhost')
    assert client.check('wrod')['blocking'] == 1
    def offline(*args, **kwargs):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx,'post',offline)
    assert client.check('word')['available'] is False


@pytest.mark.live
def test_real_language_tool():
    url = os.getenv('YUKTI_TEST_GRAMMAR')
    if not url:
        pytest.skip('YUKTI_TEST_GRAMMAR is unset')
    report = LanguageTool(url).check('Thiss sentence has a spelling mistake.')
    assert report['available'], report
    assert report['blocking'] >= 1
