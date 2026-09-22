"""Work through the sales pipeline using the VS Code cells or ``uv run --locked hands_on.py``."""

# %% [markdown]
# # Working with PySpark
# ## Goal
# Build a category sales report, check it, and run the same transformations as files arrive.
#
# Course repository: [dannyscodecorner/mastering-pyspark](https://github.com/dannyscodecorner/mastering-pyspark).
#
# This guided lab reuses the familiar sales/products example. Eight deliberately messy input rows contain the five valid sales from chapter 06 plus three rejected records. Data is synthetic. Amounts are in one unspecified currency; timestamps are UTC.
#
# **Expected final report**
#
# | category | sales | total |
# |---|---:|---:|
# | books | 3 | 50.00 |
# | games | 1 | 40.00 |
# | unmapped | 1 | 10.00 |
#
# The streaming progression adapts the original **8.3 Managing and Converting Streams** notebook: batch reader → streaming reader → shared transformations → writer/query → inspection and stop. There is no Twitter, external account or ML dependency.

# %% [markdown]
# ## Setup
# Open the **labs project folder** in VS Code. Follow `README.md` to install Java, run `uv sync --locked`, and pass `uv run --locked check_setup.py` before class.
#
# For this notebook, run `uv sync --locked --group notebook` and select the project's **.venv** Python environment in the kernel picker. The same lesson is available as `hands_on.py`, with `# %%` cells for VS Code or as a regular Python script.
#
# The next cell creates a local SparkSession and a fresh run directory. Stop the session before running setup again. The prepared input files stay unchanged; every run gets separate output and checkpoints.

# %%
from decimal import Decimal
from uuid import uuid4

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from arrival_files import publish_arrival
from workshop_runtime import DATA_ROOT, create_spark, new_run, spark_path

RUN_ROOT = new_run()
INCOMING = RUN_ROOT / "incoming"
INCOMING.mkdir()
spark = create_spark(RUN_ROOT)
print(f"Spark {spark.version}; inputs: {DATA_ROOT.name}; fresh run prepared")

# %% [markdown]
# ## Exercise 1 — Inspect the inputs
# Parquet supplies the stored schema. Here the raw amount and timestamp are strings on purpose: we still have to interpret and validate their values.

# %%
raw = spark.read.parquet(spark_path(DATA_ROOT / "sales.parquet"))
raw_products = spark.read.parquet(spark_path(DATA_ROOT / "products.parquet"))
raw.printSchema()
raw.orderBy("sale_id").show(truncate=False)
raw_products.orderBy("product_id").show(truncate=False)

# %% [markdown]
# ## Exercise 2 — Clean the keys
# ### What does `functions as F` mean?
# `pyspark.sql.functions` is a module. `F` is a short Python alias, not a separate engine.
# `F.col("product_id")` refers to a column. `F.lit("unmapped")` creates a literal value.
# The expression below describes work for Spark; `select` uses it in a new DataFrame and `show` requests rows.
#
# **Before running:** what should happen to `" b1 "` and `"g1"`?

# %%
key = F.upper(F.trim(F.col("product_id")))
raw.select("sale_id", "product_id", key.alias("clean_key")).orderBy("sale_id").show()

# %% [markdown]
# ### Reuse an expression
# A regular Python function can assemble Spark expressions. It does not become a Python UDF just because we used `def`.
# The call to `product_key` builds the expression in Python; Spark evaluates the built-in string operations on the data.
# This differs from a Python UDF, whose custom Python code runs on values in Python workers. The provided pipeline needs no UDF.


# %%
def product_key(column: Column) -> Column:
    """Build a Spark Column expression; this is not a Python UDF."""
    return F.upper(F.trim(column))


def clean_products(raw: DataFrame) -> DataFrame:
    """Normalise product keys and category names while retaining the lookup row grain."""
    return raw.select(
        product_key(F.col("product_id")).alias("product_id"),
        F.lower(F.trim("category")).alias("category"),
    )


products = clean_products(raw_products)
products.orderBy("product_id").show()

# %% [markdown]
# ## Exercise 3 — Validate the sales
# ### Parse amounts and timestamps
# Use decimal amounts and an explicit timestamp pattern. `try_cast` and `try_to_timestamp` produce null for these invalid values, allowing us to record a rejection reason. We do not silently convert a missing amount to zero.
#
# This exercise rejects missing keys, invalid/missing amounts and invalid/missing timestamps. It accepts a well-formed product key absent from the lookup; the left join will preserve that sale. A production contract could impose additional rules.


# %%
def clean_sales(raw: DataFrame) -> DataFrame:
    """Parse the exercise's UTC timestamps and amounts; retain bad input."""
    return (
        raw.withColumn("product_id", product_key(F.col("product_id")))
        .withColumn("amount", F.expr("try_cast(amount_raw AS DECIMAL(12, 2))"))
        .withColumn(
            "sold_at",
            F.try_to_timestamp("sold_at_raw", F.lit("yyyy-MM-dd HH:mm:ss")),
        )
        .withColumn(
            "reject_reason",
            F.when(
                F.col("product_id").isNull() | (F.col("product_id") == ""),
                F.lit("missing product key"),
            )
            .when(F.col("amount").isNull(), F.lit("invalid or missing amount"))
            .when(F.col("sold_at").isNull(), F.lit("invalid or missing timestamp")),
        )
    )


# %%
cleaned = clean_sales(raw)
cleaned.select("sale_id", "product_id", "amount", "sold_at", "reject_reason").orderBy(
    "sale_id"
).show(truncate=False)

# %% [markdown]
# ### Separate accepted and rejected records
# **Predict first:** which sale IDs are rejected? The invalid input remains available for diagnosis.


# %%
def accepted_sales(cleaned: DataFrame) -> DataFrame:
    """Keep parsed sales with no rejection reason, including keys absent from the lookup."""
    return cleaned.filter(F.col("reject_reason").isNull())


def rejected_sales(cleaned: DataFrame) -> DataFrame:
    """Keep invalid sales and their original values for diagnosis."""
    return cleaned.filter(F.col("reject_reason").isNotNull())


accepted = accepted_sales(cleaned)
rejected = rejected_sales(cleaned)
rejected.select("sale_id", "amount_raw", "sold_at_raw", "reject_reason").orderBy("sale_id").show(
    truncate=False
)
assert raw.count() == accepted.count() + rejected.count() == 8
assert accepted.count() == 5
assert {row.sale_id for row in rejected.select("sale_id").collect()} == {"s6", "s7", "s8"}

# %% [markdown]
# ## Exercise 4 — Join and aggregate
# Check the normalized lookup key before joining. A duplicate would multiply sales rows. The exercise labels a missing category `unmapped`; that is our reporting rule, not an automatic Spark behaviour.
#
# **Try it:** use an inner join temporarily. Which sale and amount disappear? Restore the left join before continuing.

# %%
assert products.filter(F.col("product_id").isNull() | (F.col("product_id") == "")).count() == 0
assert products.groupBy("product_id").count().filter(F.col("count") > 1).count() == 0


# %%
def enrich_sales(accepted: DataFrame, products: DataFrame) -> DataFrame:
    """Join each accepted sale to its category, retaining unmatched sales as unmapped.

    Products must have one row per key; the notebook checks that contract.
    """
    return (
        accepted.join(products, on="product_id", how="left")
        .withColumn("category", F.coalesce("category", F.lit("unmapped")))
        .select("sale_id", "product_id", "amount", "sold_at", "category")
    )


def category_totals(enriched: DataFrame) -> DataFrame:
    """Count sales and sum decimal amounts into one row per report category."""
    return enriched.groupBy("category").agg(
        F.count("*").alias("sales"), F.sum("amount").alias("total")
    )


enriched = enrich_sales(accepted, products)
report = category_totals(enriched)
report.orderBy("category").show()

# %% [markdown]
# ## Exercise 5 — Save and check the report
# These actions are deliberately simple checks over a tiny dataset. Each action can request more work; they are not a template for repeatedly counting a large production pipeline.
#
# The report should retain five accepted sales totalling 100.00. Write the rejected rows too. New output paths protect previous runs.

# %%
expected = {
    "books": (3, Decimal("50.00")),
    "games": (1, Decimal("40.00")),
    "unmapped": (1, Decimal("10.00")),
}


def snapshot(frame: DataFrame) -> dict[str, tuple[int, Decimal]]:
    """Collect the tiny classroom report into category-keyed counts and totals."""
    return {row.category: (row.sales, row.total) for row in frame.collect()}


assert enriched.count() == accepted.count() == 5
assert snapshot(report) == expected
assert enriched.agg(F.sum("amount")).first()[0] == Decimal("100.00")

report.write.mode("errorifexists").parquet(spark_path(RUN_ROOT / "report"))
rejected.write.mode("errorifexists").parquet(spark_path(RUN_ROOT / "rejected"))
saved_report = spark.read.parquet(spark_path(RUN_ROOT / "report"))
assert snapshot(saved_report) == expected
saved_report.orderBy("category").show()

# %% [markdown]
# ## Exercise 6 — Process arriving files
# ### Switch the reader
# Read an initially empty directory as a stream, using the known raw schema. Keep `products` as the same static lookup. Reuse the cleaning, accepted-row filter, left join and aggregate.
#
# This supported combination is a streaming left input with a static right lookup, followed by a category aggregate. It does not imply every batch operation is supported in streaming. Keep the lookup unchanged during this exercise.

# %%
stream_raw = spark.readStream.schema(raw.schema).parquet(spark_path(INCOMING))
stream_cleaned = clean_sales(stream_raw)
stream_accepted = accepted_sales(stream_cleaned)
stream_enriched = enrich_sales(stream_accepted, products)
stream_report = category_totals(stream_enriched)
print("batch:", report.isStreaming, "stream:", stream_report.isStreaming)

# %% [markdown]
# ### Start the query
# As in the original exercise, use a named memory table to inspect the changing result. Complete mode replaces that table with the whole current aggregate. This is a tiny classroom debugging sink, not durable output.
#
# The file source uses micro-batch execution here. A two-second trigger is a scheduling choice, not a latency guarantee. Do not call `show`, `count` or `collect` directly on `stream_report`: it is an unbounded query description.

# %%
TABLE_NAME = "sales_" + uuid4().hex[:10]
writer = (
    stream_report.writeStream.format("memory")
    .queryName(TABLE_NAME)
    .outputMode("complete")
    .option("checkpointLocation", spark_path(RUN_ROOT / "report-checkpoint"))
    .trigger(processingTime="2 seconds")
)
query = writer.start()
print("query active:", query.isActive)

# %% [markdown]
# ### Publish the first arrival
# The helper stages a complete file before exposing it in the watched folder. It refuses to publish an arrival twice. On shared object storage, the instructor supplies the equivalent file-delivery step.
#
# `processAllAvailable()` is used only to make this finite demonstration deterministic. The query itself keeps running.
#
# **Expected:** two sales, books 25.00 and games 40.00.

# %%
publish_arrival(DATA_ROOT, INCOMING, 1)
query.processAllAvailable()
current = spark.table(TABLE_NAME)
current.orderBy("category").show()
assert snapshot(current) == {"books": (1, Decimal("25.00")), "games": (1, Decimal("40.00"))}
progress = query.lastProgress
print("last completed batch:", progress["batchId"], "input rows:", progress["numInputRows"])

# %% [markdown]
# ### Add the second arrival
# Three input rows arrive: `s3`, `s4` and invalid `s6`. Only two join the report.
#
# **Expected so far:** four accepted sales; books 40.00, games 40.00 and unmapped 10.00. The total is 90.00. The memory report covers accepted sales; the third rejected record has not arrived yet.

# %%
publish_arrival(DATA_ROOT, INCOMING, 2)
query.processAllAvailable()
spark.table(TABLE_NAME).orderBy("category").show()
assert snapshot(spark.table(TABLE_NAME)) == {
    "books": (2, Decimal("40.00")),
    "games": (1, Decimal("40.00")),
    "unmapped": (1, Decimal("10.00")),
}

# %% [markdown]
# ## Exercise 7 — Resume from a checkpoint
# Stop cleanly and restart the same query with its existing checkpoint, input directory and unchanged static lookup. Then publish arrival 03.
#
# **Predict first:** will Spark count arrivals 01 and 02 again? After the last arrival the report should equal the bounded result: five sales, total 100.00.
#
# This is an orderly restart demonstration. It does not test a mid-batch crash. The checkpoint retains progress and aggregate state; a Complete-mode memory sink can recreate its table, but remains a debugging sink.

# %%
query.stop()
assert not query.isActive
query = writer.start()
try:
    publish_arrival(DATA_ROOT, INCOMING, 3)
    query.processAllAvailable()
    final_stream_report = spark.table(TABLE_NAME)
    final_stream_report.orderBy("category").show()
    assert snapshot(final_stream_report) == expected
finally:
    query.stop()
print("Restarted query reached the same report; query stopped.")

# %% [markdown]
# ## Exercise 8 — Write the streaming output
# Use a separate query and checkpoint to write accepted, enriched **rows** to Parquet in Append mode. This is not the changing aggregate from the memory-table exercise.
#
# AvailableNow consumes the input available when this query starts, using micro-batches, and then terminates. Since this is a fresh checkpoint, it processes all three existing arrival files. This lets us verify a bounded output and hand the pipeline to chapter 09.

# %%
file_query = (
    stream_enriched.writeStream.format("parquet")
    .outputMode("append")
    .option("checkpointLocation", spark_path(RUN_ROOT / "rows-checkpoint"))
    .trigger(availableNow=True)
    .start(spark_path(RUN_ROOT / "streamed-sales"))
)
try:
    if not file_query.awaitTermination(120):
        raise TimeoutError("The small exercise did not finish within 120 seconds")
finally:
    if file_query.isActive:
        file_query.stop()

stored_rows = spark.read.parquet(spark_path(RUN_ROOT / "streamed-sales"))
assert stored_rows.count() == 5
assert stored_rows.select("sale_id").distinct().count() == 5
assert snapshot(category_totals(stored_rows)) == expected
stored_rows.orderBy("sale_id").show()

# %% [markdown]
# ## Exercise 9 — Build a daily report
# Use `F.to_date("sold_at")` to add `sale_date`, then group by that date and category. Preserve the total of 100.00.
#
# | sale_date | category | total |
# |---|---|---:|
# | 2026-09-01 | books | 25.00 |
# | 2026-09-01 | games | 40.00 |
# | 2026-09-02 | books | 25.00 |
# | 2026-09-02 | unmapped | 10.00 |
#
# Work on `enriched` first. The next cell is a reference answer; hide it while participants work.

# %%
daily = (
    enriched.withColumn("sale_date", F.to_date("sold_at"))
    .groupBy("sale_date", "category")
    .agg(F.sum("amount").alias("total"))
)
daily.orderBy("sale_date", "category").show()
assert daily.count() == 4
assert daily.agg(F.sum("total")).first()[0] == Decimal("100.00")

# %% [markdown]
# ### Finish the exercise
# Both streaming queries have stopped. This exercise owns its local SparkSession, so stop it too. Keep the output and checkpoint directories for inspection. If you interrupt an interactive run, execute `spark.stop()` before running setup again.

# %%
assert not query.isActive
assert not file_query.isActive
spark.stop()
print("Checks passed: 8 inputs = 5 accepted + 3 rejected; batch and stream reports agree.")

# %% [markdown]
# ### What we reused and updated
# - Original 3.2: importing built-in functions, converting timestamps and composing column transformations.
# - Original 3.3: data exploration and inspecting transformation results. Its `split`/`explode` material remains a possible follow-up exercise, not an unexplained addition to this sales schema.
# - Original 8.3: switching static and streaming readers, using the same DataFrame operations, writer versus query handle, activity, progress, result inspection and stopping.
# - Replaced Twitter JSON and credentials with staged Parquet arrivals. Removed the hard-coded notebook environment, unconditional `coalesce(1)`, old `once=True` trigger and display polling loop. The local uv project now creates and stops its own SparkSession.
# - Added explicit validation, malformed-value handling, prepared inputs, checkpoint restart and stored-output checks.
#
# Original notebooks: [course repository, revision 8cbb218](https://github.com/PacktPublishing/Mastering-Big-Data-Analytics-with-PySpark/tree/8cbb218a87052cd1a37cbe4a7862e772c15e5e44).
# API references: [functions](https://spark.apache.org/docs/4.2.0/api/python/reference/pyspark.sql/functions.html), [Structured Streaming](https://spark.apache.org/docs/4.2.0/streaming/apis-on-dataframes-and-datasets.html), [Spark 3.5 try_to_timestamp](https://spark.apache.org/docs/3.5.8/api/python/reference/pyspark.sql/api/pyspark.sql.functions.try_to_timestamp.html).
#
# **Chapter 09:** keep the transformation functions in `pipeline.py`; configure storage, identity, dependencies, runtime and monitoring for AWS Glue separately.
