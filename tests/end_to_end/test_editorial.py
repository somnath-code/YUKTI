from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from pypdf import PdfReader
from apps.api.main import create_app
from packages.identity.access import Principal
from workers.ingestion import collect
from workers.layout_validation import check as check_layout
from workers.validation import validate


class TestVerifier:
    __test__ = False
    def __init__(self, tenant):
        self.tenant = tenant

    def verify(self, token):
        if token not in {'curator','editor','approver','reader','publisher','auditor','foreign','dual'}:
            raise ValueError('Invalid test token')
        if token == 'foreign':
            return Principal('foreign', 'another-tenant', frozenset({'editor'}))
        if token == 'dual':
            return Principal('editor', self.tenant, frozenset({'editor','approver'}))
        return Principal(token, self.tenant, frozenset({token}))


def auth(user):
    return {'Authorization': f'Bearer {user}'}


def reviewed_article(client, item):
    assert client.post('/api/articles', json=item, headers=auth('curator')).status_code == 201
    response = client.post(f"/api/articles/{item['id']}/review", headers=auth('editor'),
                           json={'source_checked':True,'grammar_reviewed':True,'rationale':'Checked the original publication.'})
    assert response.status_code == 200, response.text


def test_full_release_and_audit(runtime, catalog):
    tenure = 'test-' + uuid4().hex[:10]
    with TestClient(create_app(runtime.settings, runtime=runtime, verifier=TestVerifier(tenure))) as client:
        assert client.get('/health').json() == {'status':'ok'}
        assert client.get('/portal/').status_code == 200
        assert client.get('/console/').status_code == 200
        assert client.get('/dashboard/').status_code == 200
        assert client.get('/sutra/').status_code == 200
        assert client.get('/api/issues').status_code == 401
        assert client.get('/api/issues', headers=auth('invalid')).status_code == 401
        item = catalog['articles'][3]
        assert client.post('/api/articles', json=item, headers=auth('reader')).status_code == 403
        reviewed_article(client, item)
        assert client.post('/api/articles', json=item, headers=auth('curator')).status_code == 409
        hits = client.get('/api/search?q=differentiation&kind=peer-reviewed', headers=auth('editor'))
        assert [x['id'] for x in hits.json()] == [item['id']]
        assert client.get('/api/articles', headers=auth('foreign')).json() == []
        payload = {'title':'Test SUTRA edition','date':'2026-11-15','article_ids':[item['id']]}
        issue = client.post('/api/issues', json=payload, headers=auth('editor'))
        assert issue.status_code == 201, issue.text
        issue = issue.json()
        assert issue['state'] == 'draft'
        path = '/api/issues/' + issue['id']
        assert client.get(path + '/pdf', headers=auth('reader')).status_code == 404
        assert client.get(path + '/pdf', headers=auth('foreign')).status_code == 404
        draft = client.get(path + '/pdf', headers=auth('editor'))
        assert draft.status_code == 200
        check_layout(runtime.artifacts, issue['checksum'], 4)
        reader = PdfReader(BytesIO(draft.content))
        assert 'Bibliography' in reader.pages[-1].extract_text()
        assert 'Automatic Differentiation' in reader.pages[-1].extract_text()
        assert '[1]' in reader.pages[2].extract_text()
        assert any(a.get_object().get('/A', {}).get('/URI') == item['source']['url'] for a in reader.pages[-1]['/Annots'])
        assert 'gradient' in reader.pages[2].extract_text()
        decision = {'checksum':issue['checksum'],'note':'Read and verified this edition.'}
        assert client.post(path+'/release', headers=auth('publisher'), json=decision).status_code == 409
        assert client.post(path+'/approve', headers=auth('dual'), json=decision).status_code == 403
        assert client.post(path+'/approve', headers=auth('approver'), json={**decision,'checksum':'0'*64}).status_code == 409
        assert client.post(path+'/approve', headers=auth('approver'), json=decision).json()['state'] == 'approved'
        assert client.post(path+'/release', headers=auth('publisher'), json=decision).json()['state'] == 'released'
        assert client.post(path+'/release', headers=auth('publisher'), json=decision).status_code == 409
        assert client.get(path+'/pdf', headers=auth('reader')).content == draft.content
        events = client.get('/api/audit', headers=auth('auditor')).json()
        assert {e['action'] for e in events} >= {'issue.create','issue.approved','issue.released'}
        with runtime.db.transaction(tenure) as tx:
            assert tx.one('SELECT count(*) AS n FROM outbox WHERE tenant=%s',(tenure,))['n'] == 1
