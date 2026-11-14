import pytest

pytest.importorskip('airflow.sdk')

from workflows.airflow.dags.daily_news import daily_news
from workflows.airflow.dags.daily_research import daily_research
from workflows.airflow.dags.quality_validation import quality_validation
from workflows.airflow.dags.weekly_editorial import weekly_editorial
from workflows.airflow.dags.weekly_sutra_draft import weekly_sutra_draft


def test_five_registered_dags_and_sunday_time():
    dags = [factory() for factory in (daily_news, daily_research, quality_validation, weekly_editorial, weekly_sutra_draft)]
    assert len({dag.dag_id for dag in dags}) == 5
    assert all(str(dag.timezone) == 'Asia/Kolkata' and not dag.catchup for dag in dags)
    draft = dags[-1]
    assert draft.timetable.summary == '0 6 * * 0'
    assert draft.get_task('make_draft').upstream_task_ids == {'editorial_queue'}
    assert not any('release' in task_id or 'approve' in task_id for task_id in draft.task_ids)
