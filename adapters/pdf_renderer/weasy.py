from collections.abc import Sequence
from pathlib import Path
import re
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML
from weasyprint.urls import URLFetcher
from weasyprint.text.fonts import FontConfiguration
from packages.accessibility.checks import validate_pdf
from packages.contracts.models import Brief
from packages.core.settings import ROOT, policy
from packages.publishing.assemble import bibliography

DIRECTORY = ROOT / 'templates' / 'sutra'
STYLES = tuple('styles/' + name for name in ('theme.css', 'typography.css', 'a4-print.css', 'accessibility.css'))
TOPICS = {'ai': 'AI', 'data': 'Data engineering', 'finance': 'Finance', 'math': 'Mathematical modeling'}


class AssetFetcher(URLFetcher):
    def __init__(self, cover: Path):
        super().__init__(allowed_protocols={'file'}, allow_redirects=False, fail_on_errors=True)
        assets = (*STYLES, 'fonts/DejaVuSans.ttf', 'fonts/DejaVuSerif.ttf')
        self.allowed = {(DIRECTORY / name).as_uri() for name in assets} | {cover.as_uri()}

    def fetch(self, url: str, headers=None):
        if url not in self.allowed:
            raise ValueError('PDF renderer accepts only bundled assets')
        return super().fetch(url, headers)


def theme(magazine: dict) -> CSS:
    typography = policy('typography')
    colors = (magazine['navy'], magazine['gold'])
    families = (typography['body_family'], typography['heading_family'])
    points = typography['citation_size_pt']
    if any(not re.fullmatch(r'#[0-9a-fA-F]{6}', color) for color in colors):
        raise ValueError('Expected hexadecimal magazine colors')
    if any(not re.fullmatch(r'[A-Za-z0-9 -]+', family) for family in families) or not 7 <= points <= 16:
        raise ValueError('Invalid PDF typography')
    return CSS(string=f':root {{ --navy:{colors[0]};--gold:{colors[1]};'
                      f'--body:"{families[0]}";--heading:"{families[1]}";--citation-size:{points}pt; }}')


class WeasyRenderer:
    def render(self, title: str, issue_date: str, entries: list[dict], *, draft: bool = True,
               corrections: Sequence[str] = ()) -> tuple[bytes, int]:
        if len(corrections) > 8 or any(not 1 <= len(note) <= 350 for note in corrections):
            raise ValueError('Correction notes exceed the layout budget')
        magazine = policy('design')
        cover = (DIRECTORY / magazine['cover']).resolve()
        if cover.parent != DIRECTORY / 'covers' or cover.suffix != '.png':
            raise ValueError('Use a bundled PNG cover')
        meta = yaml.safe_load((cover.parent / 'cover-metadata.yaml').read_text(encoding='utf-8'))
        env = Environment(loader=FileSystemLoader(str(DIRECTORY / 'layouts')), autoescape=select_autoescape(['html']))
        references = bibliography([Brief.model_validate(entry) for entry in entries])
        markup = env.get_template('issue.html').render(
            title=title, date=issue_date, entries=references, draft=draft, magazine=magazine,
            cover_alt=meta['alt'], topics=TOPICS, styles=STYLES, corrections=corrections)
        document = HTML(string=markup, base_url=str(DIRECTORY) + '/', url_fetcher=AssetFetcher(cover)).render(
            stylesheets=[theme(magazine)], font_config=FontConfiguration())
        pages = len(document.pages)
        cfg = policy('print')
        if pages > cfg['max_pdf_pages']:
            raise ValueError('Issue exceeds page budget')
        data = document.write_pdf(pdf_tags=cfg['require_tags'])
        validate_pdf(data, len(entries) + 3 + bool(corrections))
        return data, pages
