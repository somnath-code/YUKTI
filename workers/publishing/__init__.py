from datetime import date

from packages.contracts.models import IssueInput
from packages.core.settings import policy
from packages.editorial.service import Editorial
from packages.identity.access import Principal


def editor_queue(editorial: Editorial, tenant: str) -> dict:
    with editorial.db.transaction(tenant) as tx:
        ready = tx.all("""SELECT id,revision FROM articles WHERE tenant=%s AND state='reviewed'
            ORDER BY id LIMIT %s""", (tenant, policy('editorial')['max_issue_articles']))
        pending = tx.one("SELECT count(*) AS n FROM articles WHERE tenant=%s AND state='draft'", (tenant,))
    return {'reviewed': ready, 'drafts_needing_review': pending['n']}


def prepare_weekly(editorial: Editorial, tenant: str, edition_date: date) -> dict:
    rows = editor_queue(editorial, tenant)['reviewed']
    if not rows:
        return {'status': 'no_reviewed_articles'}
    actor = Principal('airflow:weekly-draft', tenant, frozenset({'editor'}))
    issue = IssueInput(title=f'SUTRA weekly edition {edition_date.isoformat()}', date=edition_date,
                       article_ids=[row['id'] for row in rows])
    return editorial.create_issue(actor, issue, 'weekly-' + edition_date.isoformat())
