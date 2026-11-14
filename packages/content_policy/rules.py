from urllib.parse import urlsplit
from packages.contracts.models import Brief
from packages.core.settings import policy


def publication_error(brief: Brief) -> str | None:
    rules = policy('citations')
    source_type = policy('sources')['hosts'].get(urlsplit(brief.source.url).hostname)
    if brief.kind == 'peer-reviewed' and source_type not in rules['peer_reviewed_source_types']:
        return 'A peer-reviewed claim requires an approved journal or conference record'
    if source_type == rules['preprint_source_type'] and brief.kind != 'preprint':
        return 'Classify repository papers as preprints when citing that version'
    if brief.kind == 'preprint' and source_type != rules['preprint_source_type']:
        return 'A preprint requires a direct repository record'
    return None
