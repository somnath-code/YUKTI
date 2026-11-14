from airflow.sdk import dag
from workflows.airflow.plugins.yukti_tasks import collect_sources, schedule, start


@dag(dag_id='yukti_daily_news', schedule=schedule['daily_news'], start_date=start, catchup=False, max_active_runs=1)
def daily_news():
    collect_sources('news')


daily_news()
