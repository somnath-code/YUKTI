from packages.contracts.models import Brief


def bibliography(briefs: list[Brief]) -> list[dict]:
    entries = []
    by_url: dict[str, int] = {}
    for i, brief in enumerate(briefs, start=3):
        url = brief.source.url
        number = by_url.setdefault(url, len(by_url) + 1)
        entries.append({'page': i, 'number': number, 'article': brief})
    return entries
