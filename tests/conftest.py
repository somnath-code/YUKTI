from pathlib import Path
from dataclasses import replace
import json
import os

import pytest
from adapters.object_storage.local import LocalArtifacts
from adapters.pdf_renderer.weasy import WeasyRenderer
from adapters.postgres.store import Database
from packages.core.services import Services
from packages.core.settings import ROOT, Settings
from packages.editorial.service import Editorial


class CleanGrammar:
    def check(self, text):
        return {'available': True, 'matches': [], 'blocking': 0}


@pytest.fixture
def runtime(tmp_path):
    settings = replace(Settings(), database_url=os.getenv('YUKTI_TEST_DATABASE', f'sqlite:///{tmp_path / "test.db"}'),
                       artifacts=tmp_path / 'artifacts')
    db, storage, grammar = Database(settings.database_url), LocalArtifacts(settings.artifacts), CleanGrammar()
    return Services(settings, db, storage, grammar, Editorial(db, grammar, storage, WeasyRenderer()))


@pytest.fixture
def catalog():
    return json.loads((ROOT / 'apps/web/public/catalog.json').read_text())
