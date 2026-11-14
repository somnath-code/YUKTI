"""Run against disposable local services. Creates disposable Keycloak users."""
import base64
import hashlib
import json
import os
import re
import secrets
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4
import httpx
from packages.core.settings import ROOT

KEY = os.getenv('YUKTI_SMOKE_KEYCLOAK', 'http://localhost:18081')
API = os.getenv('YUKTI_SMOKE_API', 'http://127.0.0.1:18000')
ACTOR = os.getenv('YUKTI_SMOKE_ADMIN', 'qa-local')
TENANT = 'smoke-' + uuid4().hex[:8]
CALLBACK = 'http://localhost:8000/console/'


def assertion(response, expected):
    assert response.status_code == expected, (response.request.url.path, response.status_code, response.text[:500])
    return response


def login(username, password):
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    with httpx.Client(base_url=KEY, trust_env=False, timeout=15) as client:
        login_page = assertion(client.get('/realms/yukti/protocol/openid-connect/auth', params={
            'client_id':'yukti-console','redirect_uri':CALLBACK,'response_type':'code','scope':'openid',
            'state':'test-state','code_challenge':challenge,'code_challenge_method':'S256'}),200)
        action_match = re.search(r'<form\b[^>]*\bid="kc-form-login"[^>]*\baction="([^"]+)"', login_page.text)
        if not action_match:
            action_match = re.search(r'<form\b[^>]*\baction="([^"]+)"', login_page.text)
        assert action_match, 'Keycloak sign-in form absent'
        action = action_match.group(1).replace('&amp;', '&')
        assert urlsplit(action).netloc == urlsplit(KEY).netloc
        # HTTP clients do not apply browsers' Secure-cookie exception for localhost.
        cookies = '; '.join(f'{c.name}={c.value}' for c in client.cookies.jar)
        result = assertion(client.post(action, headers={'Cookie':cookies}, data={
            'username':username,'password':password,'credentialId':''}),302)
        params = parse_qs(urlsplit(result.headers['Location']).query)
        assert params['state'] == ['test-state']
        token = assertion(client.post('/realms/yukti/protocol/openid-connect/token', data={
            'grant_type':'authorization_code','client_id':'yukti-console','code':params['code'][0],
            'redirect_uri':CALLBACK,'code_verifier':verifier}),200).json()['access_token']
        return {'Authorization':'Bearer '+token}


def main():
    identities = {}
    with httpx.Client(base_url=KEY, trust_env=False, timeout=15) as kc:
        admin = assertion(kc.post('/realms/master/protocol/openid-connect/token',
            data={'grant_type':'password','client_id':'admin-cli','username':ACTOR,
                  'password':os.environ['YUKTI_QA_KC_ADMIN']}),200)
        kc.headers['Authorization'] = 'Bearer '+admin.json()['access_token']
        for role in ('reader','curator','editor','approver','publisher','auditor'):
            name = f'{role}-{TENANT}'
            password = secrets.token_urlsafe(26)
            created = assertion(kc.post('/admin/realms/yukti/users',json={
                'username':name,'enabled':True,'firstName':role,'lastName':'Test','emailVerified':True,
                'email':f'{name}@example.invalid','attributes':{'tenant_id':[TENANT]},
                'credentials':[{'type':'password','value':password,'temporary':False}]}),201)
            identifier = created.headers['Location'].rsplit('/',1)[-1]
            detail = assertion(kc.get('/admin/realms/yukti/roles/'+role),200).json()
            assertion(kc.post(f'/admin/realms/yukti/users/{identifier}/role-mappings/realm',json=[detail]),204)
            identities[role] = login(name,password)
    item = json.loads((ROOT/'apps/web/public/catalog.json').read_text())['articles'][2]
    item.update({'title':'Federal Reserve policy decision',
        'summary':'The committee lowered the target range for the federal funds rate.',
        'what':'The committee lowered the target range for the federal funds rate.',
        'why':'The committee cited a shift in the balance of risks.',
        'context':'The committee said inflation was still elevated.',
        'action':'It lowered the range by a quarter of a percentage point.',
        'result':'The new range was four to four and a quarter percent.'})
    with httpx.Client(base_url=API, trust_env=False, timeout=30) as client:
        assertion(client.get('/health'),200)
        assertion(client.get('/api/issues'),401)
        for role, headers in identities.items():
            session=assertion(client.get('/api/session',headers=headers),200).json()
            assert role in session['roles'] and session['tenant']==TENANT
        print('PASS Keycloak S256 PKCE, audience, realm roles and tenant claims across six users', flush=True)
        assertion(client.post('/api/articles',headers=identities['reader'],json=item),403)
        assertion(client.post('/api/articles',headers=identities['curator'],json=item),201)
        path='/api/articles/'+item['id']
        grammar=assertion(client.post(path+'/language',headers=identities['editor']),200).json()
        assert grammar['available'] and not grammar['blocking'], grammar
        decision={'source_checked':True,'grammar_reviewed':True,'rationale':'Compared the brief with the original statement.'}
        assertion(client.post(path+'/review',headers=identities['editor'],json=decision),200)
        issue=assertion(client.post('/api/issues',headers=identities['editor'],json={
            'title':'Live integration edition','date':'2026-11-15','article_ids':[item['id']]}),201).json()
        path='/api/issues/'+issue['id']
        assertion(client.get(path+'/pdf',headers=identities['reader']),404)
        preview=assertion(client.get(path+'/pdf',headers=identities['approver']),200)
        assert hashlib.sha256(preview.content).hexdigest()==issue['checksum']
        gate={'checksum':issue['checksum'],'note':'Reviewed the original PDF and its source.'}
        assertion(client.post(path+'/release',headers=identities['publisher'],json=gate),409)
        assertion(client.post(path+'/approve',headers=identities['approver'],json=gate),200)
        assertion(client.post(path+'/release',headers=identities['publisher'],json=gate),200)
        assert assertion(client.get(path+'/pdf',headers=identities['reader']),200).content==preview.content
        platform=assertion(client.get('/api/platform',headers=identities['auditor']),200).json()
        assert platform['counts']['issues']==1 and platform['publishing_schedule']['weekly_draft']=='0 6 * * 0'
        assertion(client.get('/api/platform',headers=identities['reader']),403)
        audit=assertion(client.get('/api/audit',headers=identities['auditor']),200).json()
        assert 'issue.released' in {x['action'] for x in audit}
        if os.getenv('YUKTI_TEST_OLLAMA'):
            from adapters.ollama.client import Ollama
            from packages.core.services import services
            from packages.core.settings import Settings
            from workers.indexing import index
            cfg=Settings()
            assert index(services(cfg).db,TENANT,Ollama(cfg.ollama_url,cfg.model))['indexed']==1
            result=assertion(client.get('/api/search/hybrid',headers=identities['editor'],
                                        params={'q':'Federal Reserve'}),200).json()
            assert [record['article']['id'] for record in result]==[item['id']]
            print('PASS hybrid search with real Ollama embeddings and PostgreSQL', flush=True)
    print('PASS HTTP API, LanguageTool, PDF checksum, manual approval, tenant release, audit', flush=True)
    print('Disposable test tenant:',TENANT,flush=True)


if __name__=='__main__':
    main()
