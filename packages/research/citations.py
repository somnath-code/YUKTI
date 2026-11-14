import re
from urllib.parse import unquote, urlsplit

DOI = re.compile(r'10\.\d{4,9}/[^\s<>"\x00-\x1f]+', re.IGNORECASE)


def canonical_doi(value: str) -> str:
    raw = value.strip()
    if raw.startswith('https://doi.org/'):
        raw = unquote(urlsplit(raw).path.lstrip('/'))
    if not DOI.fullmatch(raw):
        raise ValueError('Invalid DOI')
    return raw.lower()
