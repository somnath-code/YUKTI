"""Render a sample issue without changing approval or deployment state."""
import argparse
import json
from pathlib import Path
from adapters.pdf_renderer.weasy import WeasyRenderer
from packages.core.settings import ROOT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--issue', default='004')
    parser.add_argument('--output', type=Path, default=Path('var/sutra-draft.pdf'))
    parser.add_argument('--correction', action='append', default=[])
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'apps/web/public/catalog.json').read_text(encoding='utf-8'))
    issue = next((item for item in catalog['issues'] if item['id'] == args.issue), None)
    if issue is None:
        parser.error('Unknown sample issue')
    articles = {item['id']: item for item in catalog['articles']}
    pdf, pages = WeasyRenderer().render(issue['title'], issue['date'], [articles[key] for key in issue['article_ids']],
                                        corrections=args.correction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(pdf)
    print(f'{pages} pages written to {args.output}')


if __name__ == '__main__':
    main()
