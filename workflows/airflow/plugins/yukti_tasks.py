from datetime import timedelta
import os

import pendulum
from airflow.sdk import get_current_context, task

from packages.core.services import services
from packages.core.settings import Settings, policy
from workers.ingestion import collect
from workers.publishing import editor_queue, prepare_weekly
from workers.validation import validate

schedule = policy('schedule')
start = pendulum.datetime(2025, 1, 1, tz=schedule['timezone'])


def runtime():
    deps = services(Settings())
    return deps, os.getenv('SCHEDULER_TENANT', 'demo')


@task(retries=2, retry_delay=timedelta(minutes=5))
def collect_sources(group: str | None = None):
    deps, tenant = runtime()
    report = collect(deps.db, deps.artifacts, tenant, live=deps.settings.live_feeds, group=group)
    if report['errors']:
        raise RuntimeError(f"Collection failed for {', '.join(report['errors'])}")
    return report


@task
def validate_evidence():
    deps, tenant = runtime()
    report = validate(deps.db, tenant)
    if report['errors']:
        raise RuntimeError(f"{len(report['errors'])} evidence records failed validation")
    return report


@task
def editorial_queue():
    deps, tenant = runtime()
    return editor_queue(deps.editorial, tenant)


@task
def make_draft():
    deps, tenant = runtime()
    context = get_current_context()
    instant = context['data_interval_end'] or context['logical_date'] or pendulum.now('UTC')
    return prepare_weekly(deps.editorial, tenant, instant.in_timezone(schedule['timezone']).date())
