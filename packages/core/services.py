from dataclasses import dataclass
from adapters.grammar_checker.client import LanguageTool
from adapters.object_storage.local import LocalArtifacts
from adapters.pdf_renderer.weasy import WeasyRenderer
from adapters.postgres.store import Database
from packages.core.settings import Settings
from packages.editorial.service import Editorial


@dataclass(frozen=True)
class Services:
    settings: Settings
    db: Database
    artifacts: LocalArtifacts
    grammar: LanguageTool
    editorial: Editorial


def services(settings: Settings) -> Services:
    db = Database(settings.database_url)
    storage = LocalArtifacts(settings.artifacts)
    grammar = LanguageTool(settings.grammar_url)
    return Services(settings, db, storage, grammar, Editorial(db, grammar, storage, WeasyRenderer()))
