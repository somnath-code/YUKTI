from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import yaml
import os

ROOT = Path(__file__).resolve().parents[2]

POLICIES = {
    'sources': 'sources/official-sources', 'source_trust': 'sources/source-trust-policy',
    'iam': 'iam/roles', 'permissions': 'iam/permissions', 'access': 'iam/access-policies',
    'quality': 'quality/quality-thresholds', 'contracts': 'quality/data-contracts',
    'critical': 'quality/critical-rules', 'editorial': 'editorial/editorial-style-guide',
    'grammar': 'editorial/grammar-rules', 'readability': 'editorial/readability-rules',
    'words': 'editorial/word-limits', 'citations': 'editorial/citation-policy',
    'design': 'publishing/magazine', 'page': 'publishing/a4-page-spec',
    'typography': 'publishing/typography', 'print': 'publishing/print-quality',
    'schedule': 'publishing/weekly-schedule', 'ranking': 'search/ranking',
    'cache': 'search/caching',
}


@lru_cache
def policy(name: str) -> dict:
    content = yaml.safe_load((ROOT / 'config' / f'{POLICIES[name]}.yaml').read_text(encoding='utf-8'))
    if not isinstance(content, dict):
        raise ValueError(f'Invalid policy mapping: {name}')
    return content


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///var/yukti.db'))
    artifacts: Path = field(default_factory=lambda: Path(os.getenv('ARTIFACT_DIR', 'var/artifacts')))
    issuer: str = field(default_factory=lambda: os.getenv('OIDC_ISSUER', 'http://localhost:8081/realms/yukti'))
    jwks_url: str = field(default_factory=lambda: os.getenv('OIDC_JWKS_URL', 'http://localhost:8081/realms/yukti/protocol/openid-connect/certs'))
    audience: str = 'yukti-api'
    grammar_url: str = field(default_factory=lambda: os.getenv('LANGUAGETOOL_URL', 'http://localhost:8010/v2/check'))
    ollama_url: str = field(default_factory=lambda: os.getenv('OLLAMA_URL', 'http://localhost:11434'))
    model: str = field(default_factory=lambda: os.getenv('OLLAMA_MODEL', 'qwen2.5:1.5b'))
    live_feeds: bool = field(default_factory=lambda: os.getenv('LIVE_FEEDS') == '1')
