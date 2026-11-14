import re
from packages.contracts.models import Brief
from packages.core.settings import policy
from packages.provenance.sources import canonical_url, valid_date
from packages.content_policy.rules import publication_error


def words(text: str) -> int:
    return len(re.findall(r"\b\w+(?:[-’']\w+)*\b", text))


def inspect(brief: Brief) -> dict:
    errors = []
    try:
        canonical_url(brief.source.url)
        valid_date(brief.when)
        error = publication_error(brief)
        if error:
            errors.append(error)
    except ValueError as exc:
        errors.append(str(exc))
    count = words(brief.body())
    minimum, maximum = policy('words')[brief.kind]
    if not minimum <= count <= maximum:
        errors.append(f'Use {minimum}–{maximum} words across the brief sections')
    return {'passed': not errors, 'words': count, 'errors': errors,
            'readability': readability(brief.body()),
            'human_source_review_required': policy('citations')['human_review_required']}


def readability(text: str) -> dict:
    limits = policy('readability')
    sentences = [words(part) for part in re.split(r'[.!?](?=\s|$)|\n', text) if words(part)]
    average = round(sum(sentences) / len(sentences), 1) if sentences else 0
    return {'average_sentence_words': average, 'long_sentences': sum(n > limits['max_sentence_words'] for n in sentences),
            'advisory': average > limits['max_average_sentence_words']}
