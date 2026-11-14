from packages.contracts.models import Brief, Grammar


def review(brief: Brief, grammar: Grammar) -> dict:
    return grammar.check(f'{brief.title}\n{brief.body()}')
