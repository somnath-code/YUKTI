from typing import Protocol


class SuggestionModel(Protocol):
    def suggest(self, evidence: str) -> str: ...


def propose(model: SuggestionModel, evidence: str) -> dict:
    return {'suggestion': model.suggest(evidence), 'requires_review': True}
