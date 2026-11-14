import httpx
from packages.core.settings import policy


class LanguageTool:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def check(self, text: str) -> dict:
        cfg = policy('grammar')
        try:
            response = httpx.post(self.endpoint, data={'text': text, 'language': cfg['language']},
                                  timeout=12, trust_env=False)
            response.raise_for_status()
            matches = response.json()['matches']
            clean = [{'message': str(match['message'])[:500], 'offset': match['offset'],
                      'length': match['length'], 'rule': match['rule']['id'],
                      'type': match['rule']['issueType'],
                      'blocking': match['rule']['issueType'] in cfg['blocked_issue_types'],
                      'suggestions': [str(x['value'])[:120] for x in match['replacements'][:3]]}
                     for match in matches]
            return {'available': True, 'matches': clean[:cfg['max_matches']],
                    'blocking': sum(x['blocking'] for x in clean)}
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            return {'available': False, 'matches': [], 'blocking': 0}
