from airflow.sdk import dag
from workflows.airflow.plugins.yukti_tasks import schedule, start, validate_evidence


@dag(dag_id='yukti_quality_validation', schedule=schedule['quality_validation'], start_date=start, catchup=False, max_active_runs=1)
def quality_validation():
    validate_evidence()


quality_validation()
