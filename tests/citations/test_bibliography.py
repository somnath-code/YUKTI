from packages.contracts.models import Brief
from packages.publishing.assemble import bibliography
from packages.research.citations import canonical_doi
import pytest


def test_doi_and_repeated_source_are_normalized(catalog):
    assert canonical_doi('https://doi.org/10.1000/ABC.123') == '10.1000/abc.123'
    with pytest.raises(ValueError):
        canonical_doi('https://example.invalid/10.1000/abc')
    sample = Brief.model_validate(catalog['articles'][0])
    other = Brief.model_validate(catalog['articles'][1])
    refs = bibliography([sample, other, sample])
    assert [(r['page'],r['number']) for r in refs] == [(3,1),(4,2),(5,1)]
