from packages.search.hybrid import merge_ranked


def test_consensus_ranks_first_and_ties_break_on_id():
    hits = merge_ranked([{'id':'alpha'}, {'id':'shared'}], [{'id':'beta'}, {'id':'shared'}], constant=60, limit=3)
    assert [row['article']['id'] for row in hits] == ['shared', 'alpha', 'beta']
