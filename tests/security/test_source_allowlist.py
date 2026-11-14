import copy
from pathlib import Path
import re
import pytest
from pydantic import ValidationError
from defusedxml.common import EntitiesForbidden
from packages.contracts.models import Brief
from packages.core.settings import policy
from packages.ingestion.feeds import parse
from packages.provenance.sources import canonical_url
from packages.quality.checks import inspect, words
from packages.research.classification import research_papers


@pytest.mark.parametrize('url', [
    'http://arxiv.org/abs/123', 'https://arxiv.org.evil.invalid/a', 'https://arxiv.org@evil.invalid/a',
    'https://arxiv.org:8443/a', 'https://evil.invalid/a', 'https://127.0.0.1/foo', 'https://arxiv.org/a#fragment',
])
def test_source_allowlist(url):
    with pytest.raises(ValueError):
        canonical_url(url)
