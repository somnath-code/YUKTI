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


def test_jwt_issuer_audience_expiry_and_signatures(monkeypatch):
    verifier = TokenVerifier(Settings())
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    class Key:
        def __init__(self):
            self.key = key.public_key()
    monkeypatch.setattr(verifier.keys, 'get_signing_key_from_jwt', lambda token: Key())
    claims = {'sub':'editor-a','tenant_id':'demo','iss':verifier.settings.issuer,'aud':'yukti-api',
              'iat':int(time.time()),'exp':int(time.time())+60,'realm_access':{'roles':['editor']}}
    def token(values):
        return jwt.encode({**claims, **values}, key, algorithm='RS256')
    assert verifier.verify(token({})).can('article:review')
    for bad in [{'aud':'other'}, {'exp':0}, {'iss':'http://wrong.invalid'}, {'tenant_id':'../bad'}]:
        with pytest.raises(jwt.PyJWTError):
            verifier.verify(token(bad))
    with pytest.raises(jwt.PyJWTError):
        verifier.verify(jwt.encode(claims, 'x'*40, algorithm='HS256'))
