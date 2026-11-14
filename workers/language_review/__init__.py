from packages.contracts.models import Brief, Grammar
from packages.language_quality.review import review


def check(grammar: Grammar, item: dict) -> dict:
    return review(Brief.model_validate(item), grammar)
