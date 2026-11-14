from airflow.sdk import dag
from workflows.airflow.plugins.yukti_tasks import editorial_queue, schedule, start, validate_evidence


@dag(dag_id='sutra_weekly_editorial', schedule=schedule['weekly_editorial'], start_date=start, catchup=False, max_active_runs=1)
def weekly_editorial():
    validate_evidence() >> editorial_queue()


weekly_editorial()
