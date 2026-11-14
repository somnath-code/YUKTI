from datetime import date
from hashlib import sha256
from urllib.parse import urlsplit, urlunsplit
from packages.core.settings import policy

def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def canonical_url(url: str) -> str:
    if any(c.isspace() or c == '\\' for c in url):
        raise ValueError('Source URL contains invalid characters')
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname not in policy('sources')['hosts']
            or parts.netloc.lower() != parts.hostname or parts.fragment):
        raise ValueError('Use an HTTPS source on the primary-source allowlist')
    return urlunsplit(('https', parts.hostname, parts.path or '/', parts.query, ''))


def valid_date(value: str) -> None:
    parts = value.split('-')
    date(*(int(n) for n in (parts + ['1'] * (3 - len(parts)))))
