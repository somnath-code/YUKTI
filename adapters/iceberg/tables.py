import re


def append_analytics(spark, parcel, table: str) -> None:
    """Append a narrow Spark DataFrame to a preconfigured Iceberg catalog."""
    if not re.fullmatch(r'[a-z_]+\.[a-z_]+\.[a-z_]+', table):
        raise ValueError('Use catalog.namespace.table with lowercase identifiers')
    catalog, namespace, _ = table.split('.')
    spark.sql(f'CREATE NAMESPACE IF NOT EXISTS {catalog}.{namespace}')
    expected = ('tenant', 'topic', 'kind', 'records', 'sources')
    frame = parcel.select(*expected)
    if spark.catalog.tableExists(table):
        frame.writeTo(table).append()
    else:
        frame.writeTo(table).using('iceberg').create()
