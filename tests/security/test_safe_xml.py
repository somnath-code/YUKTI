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


def test_feed_parser_caps_and_xml_security():
    cfg = policy('sources')['feeds'][0]
    with pytest.raises(EntitiesForbidden):
        parse(b'<!DOCTYPE root [<!ENTITY data "example">]><root>&data;</root>', cfg)
    with pytest.raises(ValueError):
        parse(b'x' * (policy('quality')['max_feed_bytes'] + 1), cfg)
    assert parse(b'<rss><channel><item><title>Broken link</title><link>http://127.0.0.1</link></item></channel></rss>', cfg) == []
