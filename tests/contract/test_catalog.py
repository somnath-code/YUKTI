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


def test_catalog_contract_and_categories(catalog):
    articles = [Brief.model_validate(a) for a in catalog['articles']]
    ids = {a.id for a in articles}
    assert all(inspect(a)['passed'] for a in articles)
    assert len(ids) == len(articles)
    assert {a.kind for a in research_papers(articles)} == {'preprint','peer-reviewed'}
    for issue in catalog['issues']:
        assert set(issue['article_ids']) <= ids
        assert len(issue['article_ids']) == len(set(issue['article_ids']))
