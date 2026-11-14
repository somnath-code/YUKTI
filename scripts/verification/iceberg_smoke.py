"""Run the local catalog example with an explicitly downloaded Iceberg runtime JAR."""
import argparse
from pathlib import Path
from adapters.iceberg.tables import append_analytics


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jar', type=Path, required=True)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--warehouse', type=Path, required=True)
    args = p.parse_args()
    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.master('local[2]').appName('YUKTI Iceberg validation')
             .config('spark.ui.enabled','false').config('spark.jars',str(args.jar.resolve()))
             .config('spark.sql.catalog.lab','org.apache.iceberg.spark.SparkCatalog')
             .config('spark.sql.catalog.lab.type','hadoop')
             .config('spark.sql.catalog.lab.warehouse',str(args.warehouse.resolve())).getOrCreate())
    try:
        append_analytics(spark, spark.read.parquet(str(args.input)), 'lab.research.rollup')
        print(f'Iceberg records: {spark.table("lab.research.rollup").count()}')
    finally:
        spark.stop()


if __name__ == '__main__':
    main()
