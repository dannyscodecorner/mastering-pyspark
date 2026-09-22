# Small PySpark reference

These are API reminders, not completed exercise answers. `F` is the alias from `from pyspark.sql import functions as F`.

| Operation | Shape |
|---|---|
| Configure / obtain a session | `SparkSession.builder.master(...).appName(...).getOrCreate()` |
| Inspect / stop a session | `spark.version` / `spark.stop()` |
| Read prepared Parquet | `spark.read.parquet(path)` |
| Inspect schema / rows | `df.printSchema()` / `df.show(truncate=False)` |
| Reference a column / literal | `F.col("amount")` / `F.lit("unknown")` |
| String operations | `F.trim(column)`, `F.upper(column)`, `F.lower(column)` |
| Name an expression | `expression.alias("name")` |
| Select / add a column | `df.select(...)` / `df.withColumn("name", expression)` |
| Tolerant decimal parsing | `F.expr("try_cast(amount_raw AS DECIMAL(12, 2))")` |
| Tolerant timestamp parsing | `F.try_to_timestamp(column, F.lit(pattern))` |
| Null checks | `column.isNull()` / `column.isNotNull()` |
| Conditional expression | `F.when(condition, value).when(condition, value)` |
| First non-null value | `F.coalesce(column, fallback)` |
| Filter | `df.filter(condition)` |
| Join | `left.join(right, on="key", how="join_type")` |
| Group and aggregate | `df.groupBy(...).agg(...)` |
| Aggregates | `F.count("*")`, `F.sum(column)`, `F.max(column)` |
| Write Parquet | `df.write.mode("errorifexists").parquet(path)` |
| Inspect a physical plan | `df.explain(mode="formatted")` |
| Streaming reader | `spark.readStream.schema(schema).parquet(path)` |
| Running query | `writer.start()`, `query.isActive`, `query.lastProgress`, `query.stop()` |

Use `&` / `|` with parenthesised Spark column conditions, not Python `and` / `or`. Work with bounded inputs or memory-table results when inspecting rows; do not call `show()` directly on an unbounded streaming DataFrame.

Versioned documentation: [PySpark 4.2 functions](https://spark.apache.org/docs/4.2.0/api/python/reference/pyspark.sql/functions.html) · [DataFrame API](https://spark.apache.org/docs/4.2.0/api/python/reference/pyspark.sql/dataframe.html) · [Structured Streaming](https://spark.apache.org/docs/4.2.0/streaming/apis-on-dataframes-and-datasets.html).
