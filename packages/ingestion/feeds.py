from dataclasses import asdict, dataclass
from pathlib import Path
import re
from xml.etree.ElementTree import Element
import httpx
from defusedxml.ElementTree import fromstring
from packages.core.settings import ROOT, policy
from packages.provenance.sources import canonical_url


@dataclass(frozen=True)
class Candidate:
    title: str
    url: str
    raw_text: str
    published: str
    topic: str
    kind: str
    publisher: str

    def as_record(self) -> dict:
        return asdict(self)


def read_feed(url: str) -> bytes:
    cfg = policy('quality')
    try:
        with httpx.stream('GET', canonical_url(url), follow_redirects=policy('source_trust')['allow_redirects'], trust_env=False,
                          timeout=httpx.Timeout(10, connect=5),
                          headers={'User-Agent': 'YUKTI-research/1.0 (metadata collection)'}) as response:
            response.raise_for_status()
            chunks = bytearray()
            for chunk in response.iter_bytes():
                chunks.extend(chunk)
                if len(chunks) > cfg['max_feed_bytes']:
                    raise ValueError('Feed exceeds byte budget')
            return bytes(chunks)
    except httpx.HTTPError as exc:
        raise ValueError('Authoritative feed is unavailable') from exc


def parse(data: bytes, feed: dict) -> list[Candidate]:
    cfg = policy('quality')
    if len(data) > cfg['max_feed_bytes']:
        raise ValueError('Feed exceeds byte budget')
    root = fromstring(data)
    rows = (root.findall('./channel/item') or root.findall('{*}entry'))[:cfg['max_items_per_feed']]

    def value(row: Element, *names: str) -> str:
        for name in names:
            item = row.find('{*}' + name)
            if item is not None:
                text = ' '.join(''.join(item.itertext()).split())
                return item.get('href', text)
        return ''

    candidates = {}
    for row in rows:
        title = value(row, 'title')[:300]
        if not title:
            continue
        url = value(row, 'id', 'link') if feed['kind'] == 'preprint' else value(row, 'link')
        if feed['kind'] == 'preprint':
            url = re.sub(r'^http://(arxiv\.org/abs/)', r'https://\1', url)
        try:
            url = canonical_url(url)
        except ValueError:
            continue
        candidate = Candidate(title, url, value(row, 'summary', 'description')[:cfg['max_raw_text']],
                              value(row, 'published', 'pubDate', 'updated')[:70], feed['topic'],
                              feed['kind'], feed['publisher'])
        candidates[url] = candidate
    return list(candidates.values())


def snapshot(feed_id: str, live: bool) -> tuple[dict, bytes]:
    feed = next(item for item in policy('sources')['feeds'] if item['id'] == feed_id)
    if live:
        return feed, read_feed(feed['url'])
    return feed, (ROOT / 'database' / 'seeds' / f'{feed_id}.xml').read_bytes()
