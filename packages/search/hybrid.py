def merge_ranked(*lists: list[dict], constant: int, limit: int) -> list[dict]:
    records: dict[str, dict] = {}
    scores: dict[str, float] = {}
    for hits in lists:
        for rank, article in enumerate(hits, start=1):
            identifier = article['id']
            records[identifier] = article
            scores[identifier] = scores.get(identifier, 0.0) + 1 / (constant + rank)
    ordered = sorted(records, key=lambda identifier: (-scores[identifier], identifier))
    return [{'article': records[key], 'score': scores[key]} for key in ordered[:limit]]
