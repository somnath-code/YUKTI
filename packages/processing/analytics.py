from pathlib import Path


def summarise(spark, source: Path, target: Path) -> int:
    from pyspark.sql.functions import col, count, count_distinct
    frame = spark.read.schema('topic STRING, kind STRING, url STRING, tenant STRING').json(str(source))
    valid = frame.filter(col('topic').isin('ai','data','finance','math') & col('url').startswith('https://'))
    summary = valid.groupBy('tenant', 'topic', 'kind').agg(count('*').alias('records'),
                                                         count_distinct('url').alias('sources'))
    summary.write.mode('overwrite').parquet(str(target))
    return spark.read.parquet(str(target)).count()
