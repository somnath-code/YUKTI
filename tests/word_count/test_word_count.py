from packages.quality.checks import readability, words


def test_hyphens_apostrophes_and_readability():
    assert words("well-tested analyst’s paper") == 3
    assert readability('Short sentence. ' + 'word ' * 55)['long_sentences'] == 1
    assert not readability('Plain English reads well.')['advisory']
