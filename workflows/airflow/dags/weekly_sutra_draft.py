from airflow.sdk import dag
from workflows.airflow.plugins.yukti_tasks import editorial_queue, make_draft, schedule, start, validate_evidence


@dag(dag_id='sutra_draft_weekly', schedule=schedule['weekly_draft'], start_date=start, catchup=False, max_active_runs=1)
def weekly_sutra_draft():
    validate_evidence() >> editorial_queue() >> make_draft()


weekly_sutra_draft()
