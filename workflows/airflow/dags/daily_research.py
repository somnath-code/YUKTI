from airflow.sdk import dag
from workflows.airflow.plugins.yukti_tasks import collect_sources, schedule, start


@dag(dag_id='yukti_daily_research', schedule=schedule['daily_research'], start_date=start, catchup=False, max_active_runs=1)
def daily_research():
    collect_sources('research')


daily_research()
