import json
from uuid import uuid4
from adapters.messaging.outbox import enqueue
from adapters.postgres.store import Database
from packages.contracts.models import ArtifactStore, Brief, EditorialReview, Grammar, IssueDecision, IssueInput, Renderer
from packages.core.events import audit, encoded
from packages.core.settings import policy
from packages.identity.access import Principal
from packages.language_quality.review import review
from packages.provenance.sources import canonical_url
from packages.quality.checks import inspect


class Problem(Exception):
    def __init__(self, code: int, detail: str | dict):
        self.code, self.detail = code, detail
        super().__init__(str(detail))


class Editorial:
    def __init__(self, db: Database, grammar: Grammar, artifacts: ArtifactStore, renderer: Renderer):
        self.db, self.grammar, self.artifacts, self.renderer = db, grammar, artifacts, renderer

    def submit(self, user: Principal, brief: Brief, expected: int | None = None) -> dict:
        report = inspect(brief)
        if not report['passed']:
            raise Problem(422, report)
        source = canonical_url(brief.source.url)
        values = (source, encoded(brief.model_dump()), user.tenant, brief.id)
        with self.db.transaction(user.tenant, write=True) as tx:
            if expected is None:
                row = tx.one(
                    """INSERT INTO articles(source_url,payload,tenant,id) VALUES (%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING RETURNING id,revision,state""", values)
            else:
                row = tx.one(
                    """UPDATE articles SET source_url=%s,payload=%s,revision=revision+1,
                    state='draft',reviewed_by=NULL,review=NULL WHERE tenant=%s AND id=%s
                    AND revision=%s RETURNING id,revision,state""", (*values, expected))
            if row is None:
                raise Problem(409, 'Article or source exists, or revision no longer matches')
            audit(tx, user.tenant, user.subject, 'article.edit' if expected else 'article.ingest', brief.id,
                  {'revision': row['revision']})
            return {**row, 'quality': report}

    def row(self, tx, tenant: str, table: str, identifier: str) -> dict:
        # Only internal table names are accepted.
        if table not in {'articles', 'issues'}:
            raise ValueError('Unexpected record type')
        row = tx.one(f'SELECT * FROM {table} WHERE tenant=%s AND id=%s', (tenant, identifier))
        if row is None:
            raise Problem(404, 'Record not found')
        return row

    def review_article(self, user: Principal, identifier: str, decision: EditorialReview) -> dict:
        with self.db.transaction(user.tenant) as tx:
            row = self.row(tx, user.tenant, 'articles', identifier)
        brief = Brief.model_validate_json(row['payload'])
        checks = review(brief, self.grammar)
        if not checks['available']:
            raise Problem(503, 'LanguageTool unavailable. Review can be retried when it recovers.')
        if checks['blocking']:
            raise Problem(422, {'message': 'Correct the blocking language findings and resubmit', 'grammar': checks})
        with self.db.transaction(user.tenant, write=True) as tx:
            updated = tx.one("""UPDATE articles SET state='reviewed',reviewed_by=%s,review=%s
                WHERE tenant=%s AND id=%s AND revision=%s AND state='draft' RETURNING id,state,revision""",
                (user.subject, encoded(decision.model_dump()), user.tenant, identifier, row['revision']))
            if not updated:
                raise Problem(409, 'Article has changed or is already reviewed')
            audit(tx, user.tenant, user.subject, 'article.review', identifier, {'revision': row['revision']})
            return updated

    def create_issue(self, user: Principal, issue: IssueInput, identifier: str | None = None) -> dict:
        identifiers = issue.article_ids
        if len(set(identifiers)) != len(identifiers):
            raise Problem(422, 'Each article may appear once per issue')
        identifier = identifier or uuid4().hex
        with self.db.transaction(user.tenant) as tx:
            existing = tx.one('SELECT * FROM issues WHERE tenant=%s AND id=%s', (user.tenant, identifier))
            if existing:
                return self.issue_metadata(existing)
            articles = [self.row(tx, user.tenant, 'articles', item) for item in identifiers]
        if any(row['state'] != 'reviewed' for row in articles):
            raise Problem(422, 'Each article must have an editorial review')
        snapshot = [{**json.loads(row['payload']), 'revision': row['revision']} for row in articles]
        try:
            pdf, pages = self.renderer.render(issue.title, issue.date.isoformat(),
                                              [json.loads(row['payload']) for row in articles], draft=False)
        except ValueError as error:
            raise Problem(422, 'The draft failed PDF layout validation') from error
        checksum = self.artifacts.put(pdf)
        with self.db.transaction(user.tenant, write=True) as tx:
            inserted = tx.one("""INSERT INTO issues(tenant,id,title,edition_date,state,checksum,page_count,snapshot,created_by)
                VALUES (%s,%s,%s,%s,'draft',%s,%s,%s,%s)
                ON CONFLICT DO NOTHING RETURNING id""",
                (user.tenant, identifier, issue.title, issue.date.isoformat(), checksum, pages, encoded(snapshot), user.subject))
            if inserted:
                audit(tx, user.tenant, user.subject, 'issue.create', identifier, {'checksum': checksum})
            return self.issue_metadata(self.row(tx, user.tenant, 'issues', identifier))

    def advance(self, user: Principal, identifier: str, decision: IssueDecision, release: bool = False) -> dict:
        before, after, actor_column = ('approved', 'released', 'released_by') if release else ('draft', 'approved', 'approved_by')
        with self.db.transaction(user.tenant, write=True) as tx:
            row = self.row(tx, user.tenant, 'issues', identifier)
            if row['checksum'] != decision.checksum or row['state'] != before:
                raise Problem(409, 'Issue state or reviewed PDF checksum has changed')
            if policy('access')['three_distinct_issue_actors'] and user.subject in {row['created_by'], row['approved_by']}:
                raise Problem(403, 'Create, approve and release require distinct users')
            try:
                self.artifacts.get(row['checksum'])
            except OSError as exc:
                raise Problem(409, 'The reviewed PDF is missing or damaged') from exc
            updated = tx.one(f"""UPDATE issues SET state=%s,{actor_column}=%s WHERE tenant=%s
                AND id=%s AND state=%s AND checksum=%s RETURNING id""",
                (after, user.subject, user.tenant, identifier, before, decision.checksum))
            if not updated:
                raise Problem(409, 'Issue state has changed')
            if release:
                enqueue(tx, user.tenant, f'issue-release-{identifier}', 'issue.released', {'checksum': row['checksum']})
            audit(tx, user.tenant, user.subject, f'issue.{after}', identifier, decision.model_dump())
            return self.issue_metadata(self.row(tx, user.tenant, 'issues', identifier))

    @staticmethod
    def issue_metadata(row: dict) -> dict:
        return {key: row[key] for key in ('id', 'title', 'edition_date', 'state', 'checksum', 'page_count')}
