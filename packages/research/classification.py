from packages.contracts.models import Brief


def research_papers(articles: list[Brief]) -> list[Brief]:
    return [article for article in articles if article.kind in {'peer-reviewed', 'preprint'}]
