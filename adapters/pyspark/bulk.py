from pathlib import Path
from packages.processing.analytics import summarise


def run(input_path: Path, output_path: Path) -> int:
    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.master('local[2]').appName('YUKTI evidence analytics')
             .config('spark.ui.enabled', 'false').config('spark.sql.shuffle.partitions', '2')
             .config('spark.driver.bindAddress', '127.0.0.1').config('spark.driver.host', '127.0.0.1')
             .getOrCreate())
    try:
        return summarise(spark, input_path, output_path)
    finally:
        spark.stop()
