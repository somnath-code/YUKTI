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


def test_invalid_date_paper_label_and_bounds(catalog):
    data = copy.deepcopy(catalog['articles'][-1])
    data['kind'] = 'peer-reviewed'
    assert not inspect(Brief.model_validate(data))['passed']
    data['kind'] = 'preprint'
    data['when'] = '2026-02-30'
    assert not inspect(Brief.model_validate(data))['passed']
    data['id'] = '../unsafe'
    with pytest.raises(ValidationError):
        Brief.model_validate(data)
    assert words("well-tested analyst’s preprint") == 3
