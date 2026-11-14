from contextlib import asynccontextmanager
from typing import Annotated
import json
import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from psycopg.errors import UniqueViolation
from sqlite3 import IntegrityError

from adapters.identity_provider.tokens import TokenVerifier
from adapters.ollama.client import Ollama
from adapters.search_engine.full_text import search
from adapters.vector_store.sql import nearest
from packages.contracts.models import Brief, EditorialReview, IssueDecision, IssueInput, Kind, Topic
from packages.core.services import services
from packages.core.settings import ROOT, Settings, policy
from packages.editorial.service import Problem
from packages.identity.access import Principal
from packages.quality.checks import inspect
from packages.search.hybrid import merge_ranked
from workers.inference import suggest

bearer = HTTPBearer(auto_error=False)


def create_app(settings: Settings | None = None, *, runtime=None, verifier=None) -> FastAPI:
    cfg = settings or Settings()
    deps = runtime or services(cfg)
    verify = verifier or TokenVerifier(cfg)
    model = Ollama(cfg.ollama_url, cfg.model)

    @asynccontextmanager
    async def lifespan(app):
        deps.db.migrate()
        yield

    app = FastAPI(title='YUKTI Research Intelligence', version='1.1.0', lifespan=lifespan)

    @app.middleware('http')
    async def headers(req: Request, call):
        response = await call(req)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if req.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = policy('cache')['http_cache_control']
        if req.url.path.startswith(('/portal', '/console', '/dashboard', '/sutra')):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
                f"connect-src 'self' {cfg.issuer.split('/realms/')[0]}; style-src 'self'; img-src 'self' data:"
            )
        return response

    @app.exception_handler(Problem)
    async def problem(req, exc):
        return JSONResponse({'detail': exc.detail}, status_code=exc.code)

    @app.exception_handler(UniqueViolation)
    @app.exception_handler(IntegrityError)
    async def conflict(req, exc):
        return JSONResponse({'detail': 'Conflicting record'}, status_code=409)

    def principal(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> Principal:
        if credentials:
            try:
                return verify.verify(credentials.credentials)
            except (jwt.PyJWTError, ValueError, KeyError, TypeError, AttributeError):
                pass
        raise HTTPException(401, 'A valid Keycloak access token is required', {'WWW-Authenticate': 'Bearer'})

    def require(permission: str):
        def allowed(user: Annotated[Principal, Depends(principal)]) -> Principal:
            if not user.can(permission):
                raise HTTPException(403, 'The current role does not grant this action')
            return user
        return allowed

    @app.get('/health')
    def health():
        with deps.db.transaction('health-check') as tx:
            tx.run('SELECT 1')
        return {'status': 'ok'}

    @app.get('/metrics', include_in_schema=False)
    def metrics():
        return Response('# TYPE yukti_up gauge\nyukti_up 1\n', media_type='text/plain')

    @app.get('/', include_in_schema=False)
    def home():
        return RedirectResponse('/portal/')

    @app.get('/api/session')
    def session(user: Annotated[Principal, Depends(principal)]):
        return {'subject': user.subject, 'tenant': user.tenant, 'roles': sorted(user.roles)}

    @app.get('/ui-config', include_in_schema=False)
    def ui_config():
        return {'issuer': cfg.issuer, 'client_id': 'yukti-console'}

    @app.put('/api/articles/{identifier}')
    def edit(identifier: str, item: Brief, revision: Annotated[int, Query(ge=1)],
             user: Annotated[Principal, Depends(require('article:edit'))]):
        if identifier != item.id:
            raise HTTPException(422, 'Article ID cannot change')
        return deps.editorial.submit(user, item, revision)

    @app.post('/api/articles', status_code=201)
    def ingest(item: Brief, user: Annotated[Principal, Depends(require('article:ingest'))]):
        return deps.editorial.submit(user, item)

    @app.post('/api/quality')
    def quality(item: Brief, user: Annotated[Principal, Depends(require('draft:read'))]):
        return inspect(item)

    @app.get('/api/articles')
    def articles(user: Annotated[Principal, Depends(require('draft:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            return [{**json.loads(x.pop('payload')), **x} for x in tx.all('SELECT payload,revision,state FROM articles WHERE tenant=%s ORDER BY id LIMIT 100', (user.tenant,))]

    @app.get('/api/evidence')
    def evidence(user: Annotated[Principal, Depends(require('draft:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            return [{**json.loads(x.pop('metadata')), **x} for x in tx.all(
                '''SELECT e.urn,e.metadata,e.checksum,e.collected_at FROM evidence e
                WHERE e.tenant=%s AND NOT EXISTS (SELECT 1 FROM evidence_quarantine q
                  WHERE q.tenant=e.tenant AND q.urn=e.urn) ORDER BY e.collected_at DESC LIMIT 60''',
                (user.tenant,))]

    @app.post('/api/evidence/{urn}/suggest')
    def suggestion(urn: str, user: Annotated[Principal, Depends(require('article:edit'))]):
        try:
            return suggest(deps.db, user.tenant, urn, model)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise HTTPException(503, 'Ollama model unavailable') from exc

    @app.post('/api/articles/{identifier}/language')
    def language(identifier: str, user: Annotated[Principal, Depends(require('draft:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            row = deps.editorial.row(tx, user.tenant, 'articles', identifier)
        from workers.language_review import check
        return check(deps.grammar, json.loads(row['payload']))

    @app.post('/api/articles/{identifier}/review')
    def review(identifier: str, decision: EditorialReview, user: Annotated[Principal, Depends(require('article:review'))]):
        return deps.editorial.review_article(user, identifier, decision)

    @app.get('/api/search')
    def find(user: Annotated[Principal, Depends(require('draft:read'))], q: Annotated[str, Query(max_length=120)] = '',
             topic: Topic | None = None, kind: Kind | None = None, limit: Annotated[int, Query(ge=1, le=50)] = 20):
        with deps.db.transaction(user.tenant) as tx:
            return [json.loads(row['payload']) for row in search(tx, user.tenant, q, topic, kind, limit)]

    @app.get('/api/semantic')
    def semantic(user: Annotated[Principal, Depends(require('draft:read'))], q: Annotated[str, Query(min_length=2, max_length=500)]):
        try:
            values = model.embed(q)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise HTTPException(503, 'Ollama embedding model unavailable') from exc
        with deps.db.transaction(user.tenant) as tx:
            return nearest(tx, user.tenant, model.embedding_model, values)

    @app.get('/api/search/hybrid')
    def hybrid(user: Annotated[Principal, Depends(require('draft:read'))],
               q: Annotated[str, Query(min_length=2, max_length=120)]):
        cfg = policy('ranking')
        limit = cfg['default_limit']
        try:
            values = model.embed(q)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise HTTPException(503, 'Ollama embedding model unavailable') from exc
        with deps.db.transaction(user.tenant) as tx:
            keyword = [json.loads(row['payload']) for row in search(tx, user.tenant, q, None, None, limit)]
            semantic = [row['article'] for row in nearest(tx, user.tenant, model.embedding_model, values, limit)]
        return merge_ranked(keyword, semantic, constant=cfg['rrf_constant'], limit=limit)

    @app.get('/api/platform')
    def platform(user: Annotated[Principal, Depends(require('audit:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            counts = {table: tx.one(f'SELECT count(*) AS n FROM {table} WHERE tenant=%s', (user.tenant,))['n']
                      for table in ('articles', 'evidence', 'evidence_quarantine', 'issues')}
        return {'tenant': user.tenant, 'counts': counts, 'roles': policy('iam'),
                'publishing_schedule': policy('schedule')}

    @app.post('/api/issues', status_code=201)
    def create_issue(item: IssueInput, user: Annotated[Principal, Depends(require('issue:create'))]):
        return deps.editorial.create_issue(user, item)

    @app.get('/api/issues')
    def issues(user: Annotated[Principal, Depends(require('archive:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            sql = 'SELECT id,title,edition_date,state,checksum,page_count FROM issues WHERE tenant=%s'
            if not user.can('draft:read'):
                sql += " AND state='released'"
            return tx.all(sql + ' ORDER BY edition_date DESC,id DESC LIMIT 100', (user.tenant,))

    @app.get('/api/issues/{identifier}/pdf')
    def pdf(identifier: str, user: Annotated[Principal, Depends(require('archive:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            row = deps.editorial.row(tx, user.tenant, 'issues', identifier)
        if row['state'] != 'released' and not user.can('draft:read'):
            raise HTTPException(404, 'Record not found')
        try:
            data = deps.artifacts.get(row['checksum'])
        except OSError as exc:
            raise HTTPException(503, 'PDF unavailable') from exc
        return Response(data, media_type='application/pdf',
                        headers={'ETag': '"' + row['checksum'] + '"', 'Content-Disposition': 'inline; filename="sutra.pdf"'})

    @app.post('/api/issues/{identifier}/approve')
    def approve(identifier: str, item: IssueDecision, user: Annotated[Principal, Depends(require('issue:approve'))]):
        return deps.editorial.advance(user, identifier, item)

    @app.post('/api/issues/{identifier}/release')
    def release(identifier: str, item: IssueDecision, user: Annotated[Principal, Depends(require('issue:release'))]):
        return deps.editorial.advance(user, identifier, item, release=True)

    @app.get('/api/audit')
    def audits(user: Annotated[Principal, Depends(require('audit:read'))]):
        with deps.db.transaction(user.tenant) as tx:
            return [{**row, 'details': json.loads(row['details'])} for row in tx.all(
                'SELECT * FROM audit_log WHERE tenant=%s ORDER BY occurred_at DESC LIMIT 100', (user.tenant,))]

    for route, folder in (('portal', 'web/public'), ('console', 'admin-console'), ('dashboard', 'dashboard'), ('sutra', 'sutra')):
        app.mount('/' + route, StaticFiles(directory=ROOT / 'apps' / folder, html=True), name=route)
    return app


app = create_app()
