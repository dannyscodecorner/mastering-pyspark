"""Authoring source and complete reference; learners open notebooks/01-inspect.ipynb.

Each task has one learner starter. Optional zoom-ins enrich the same exercise;
separate deeper investigations reuse the same saved learner functions.
"""


# %% [markdown] id=welcome
# # Working with PySpark
#
# Seven shared exercises. Complete the core for an approximately 60-minute lab; choose optional zoom-ins within each exercise for more depth. Larger investigations have their own notebooks. [Start here](README.md).
#
# The data is synthetic. Amounts use one unspecified currency; timestamps are UTC.


# %% [markdown] id=setup
# ## Setup — supplied
#
# Complete the [setup check](README.md#2-create-the-virtual-environment) first. Select the lab's `.venv` kernel in VS Code, then run the next cell. It should print `Spark 4.2.0; inputs: data; fresh run prepared`.
#
# If you already have a session running, run the [cleanup cell](#cleanup) before repeating setup. To replay streaming, use the [stream recovery instructions](RECOVERY.md#exercise-6); do not delete a checkpoint or publish the same arrival twice.

# %% id=setup-code
from pathlib import Path
from uuid import uuid4

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

import lab_checks as check
from arrival_files import publish_arrival
from workshop_runtime import DATA_ROOT, create_spark, finish_query, new_run, spark_path

RUN_ROOT = new_run()
INCOMING = RUN_ROOT / "incoming"
INCOMING.mkdir()
spark = create_spark(RUN_ROOT)
print(f"Spark {spark.version}; inputs: {DATA_ROOT.name}; fresh run prepared")


# %% [markdown] id=exercise-1 role=prompt
# ---
# <a id="exercise-1"></a>
# ## Exercise 1 — Inspect the inputs
#
# **What needs attention before we can report on these sales?**
#
# Core budget: about 5 minutes.
#
# Read `data/sales.parquet` into `raw` and `data/products.parquet` into `raw_products`. Paths are supplied below. Inspect their schemas and a small sample of their rows before deciding what to clean.


# %% id=input-paths
SALES_PATH = spark_path(DATA_ROOT / "sales.parquet")
PRODUCTS_PATH = spark_path(DATA_ROOT / "products.parquet")


# %% [markdown] id=read-task role=prompt
# ### Your code — read both inputs


# %% [starter] id=read-inputs-guided replaces=read-inputs
# raw = spark.read.parquet(todo("1: supply the sales path"))
# raw_products = spark.read.parquet(todo("1: supply the products path"))


# %% id=read-inputs role=task
raw = spark.read.parquet(SALES_PATH)
raw_products = spark.read.parquet(PRODUCTS_PATH)


# %% [markdown] id=inspect-task
# ### Inspect the result
#
# Run these supplied inspection cells. Which problems are visible in the schema, and which only appear in the values?


# %% id=inspect-sales
raw.printSchema()
raw.orderBy("sale_id").show(truncate=False)


# %% id=inspect-products
raw_products.printSchema()
raw_products.orderBy("product_id").show(truncate=False)


# %% [markdown] id=input-observations role=response
# ### Your observations
#
# Double-click this Markdown cell and record at least two things you would investigate:
#
# - …
# - …
#
# What does one row represent in each input?


# %% [markdown] id=input-check-label
# ### Check
#
# You should have eight sales and three product rows. The raw sales have four columns.


# %% id=check-inputs role=check
check.inputs(raw, raw_products)


# %% [markdown] id=hints-1 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# The batch reader belongs to `spark.read`. Parquet carries its stored schema.
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# Look at key casing and spaces, the types of amount/timestamp fields, and values that do not fit those types.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-1). [Worked solution]({{solution}}.ipynb#exercise-1) — open it separately when you are ready to compare.


# %% [markdown] id=input-depth depth=zoom
# ### Why inspect before cleaning?
#
# `raw` describes one attempted sale per row. `raw_products` describes one product category per key. A string schema can faithfully store both `"25.00"` and `"oops"`; it cannot tell you that either is a valid amount. Do not infer data quality from a successful file read.
#
# The optional [schemas experiment](#extension-schemas) revisits the same records as CSV. That notebook is available after Exercise 3, when your validation function is saved.


# %% [markdown] id=exercise-2 role=prompt
# ---
# <a id="exercise-2"></a>
# ## Exercise 2 — Clean the keys
#
# **How can differently written product keys match reliably?**
#
# Core budget: about 5 minutes.
#
# Make a reusable `product_key(column)` function: trim spaces and uppercase the key. Then create `clean_products(raw)` so it returns `product_id` and `category`, with trimmed lowercase categories. Use `product_key` inside it.
#
# Success examples: `" b1 "` → `B1`, `"g1"` → `G1`, `" Books "` → `books`. Keep the original inputs available.


# %% [markdown] id=functions-note
# `F` is the alias from `from pyspark.sql import functions as F`. These functions build Spark expressions. `F.col(...)` selects a column; `F.lit(...)` describes a literal value.
#
# ### Your code — the key expression


# %% [starter] id=product-key-starter replaces=product-key
# def product_key(column: Column) -> Column:
#     """Build the normalised product-key expression."""
#     return todo("2: trim the Column, then uppercase it")


# %% id=product-key role=task
def product_key(column: Column) -> Column:
    """Build a Spark Column expression; this is not a Python UDF."""
    return F.upper(F.trim(column))


# %% [markdown] id=clean-products-label
# ### Supplied — apply your helper to the lookup
#
# This wrapper is supplied. It uses your `product_key` function.


# %% id=clean-products role=supplied
def clean_products(raw: DataFrame) -> DataFrame:
    """Normalise product keys and category names while retaining the lookup row grain."""
    return raw.select(
        product_key(F.col("product_id")).alias("product_id"),
        F.lower(F.trim("category")).alias("category"),
    )


# %% id=show-clean-products
products = clean_products(raw_products)
products.orderBy("product_id").show()
raw.select("product_id", product_key(F.col("product_id")).alias("clean_key")).show()


# %% [markdown] id=clean-check-label
# ### Check
#
# The helper verifies your expression and the lookup values. The raw data must remain unchanged.


# %% id=check-keys role=check
check.keys(raw, products, product_key)


# %% [markdown] id=hints-2 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# Use the built-in string functions for trimming and changing case.
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# Compose the operations from the inside out. Use `.alias(...)` when a derived expression needs a predictable output column name.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-2). [Worked solution]({{solution}}.ipynb#exercise-2) — open it separately when you are ready to compare.


# %% [markdown] id=key-depth depth=zoom
# ### A Python helper is not necessarily a Python UDF
#
# Calling `product_key` constructs a `Column` expression in Python. Spark evaluates its built-in operations on the data. There is no custom Python row function or UDF here.
#
# `select` creates a new DataFrame description. It does not alter `raw`. The next optional task lets you compare their schemas and try renaming/dropping columns.


# %% [markdown] id=expression-zoom role=prompt depth=zoom
# ---
# ### Expressions and immutability
#
# From `raw`, make an `exploration` DataFrame that adds a normalised `clean_key`, renames `amount_raw` to `source_amount`, and drops `sold_at_raw`. Inspect both schemas. Keep `raw` unchanged.


# %% [starter] id=expression-experiment-starter replaces=expression-experiment depth=zoom
# exploration = todo("Add a derived column, rename one, and drop another in a separate DataFrame")


# %% id=expression-experiment role=task depth=zoom
exploration = (
    raw.withColumn("clean_key", product_key(F.col("product_id")))
    .withColumnRenamed("amount_raw", "source_amount")
    .drop("sold_at_raw")
)
exploration.printSchema()
raw.printSchema()


# %% id=check-expression role=check depth=zoom
check.projection(raw, exploration)


# %% [markdown] id=expression-hint role=hint depth=zoom
# <details><summary>Hint</summary>
#
# Try `withColumn`, `withColumnRenamed` and `drop`. Keep their returned DataFrame under a new name.
#
# </details>


# %% [markdown] id=exercise-3 role=prompt
# ---
# <a id="exercise-3"></a>
# ## Exercise 3 — Validate the sales
#
# **Which rows belong in the report, and how will we explain the rejects?**
#
# Core budget: about 5 minutes.
#
# Our contract rejects missing/empty product keys, invalid or missing amounts, and invalid or missing timestamps. Keep the raw values and a `reject_reason`. A valid key absent from the lookup is still an accepted sale.
#
# Parse amounts as `DECIMAL(12, 2)` and timestamps with `yyyy-MM-dd HH:mm:ss`. Parsing failures should become null, so we can explain them. Do not silently turn missing amounts into zero.


# %% [markdown] id=predict-rejects role=response
# ### Predict before running
#
# Which sale IDs will fail this contract? Does a missing product lookup make a sale invalid?
#
# Your prediction: …


# %% [markdown] id=parse-label
# ### Supplied — parse and mark bad rows
#
# This parsing function is supplied for the core. Read its rules before using it; the optional section lets you build the parsing expressions yourself.


# %% id=clean-sales role=supplied
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


# %% id=inspect-cleaned
cleaned = clean_sales(raw)
cleaned.select("sale_id", "product_id", "amount", "sold_at", "reject_reason").orderBy(
    "sale_id"
).show(truncate=False)


# %% [markdown] id=filters-label
# ### Your code — separate accepted and rejected rows
#
# Keep the filtering functions reusable: the stream will call them too.


# %% [starter] id=split-sales-starter replaces=split-sales
# def accepted_sales(cleaned: DataFrame) -> DataFrame:
#     """Return sales without a rejection reason."""
#     return cleaned.filter(todo("3: select rows with no reject_reason"))
#
#
# def rejected_sales(cleaned: DataFrame) -> DataFrame:
#     """Return rejected sales, keeping their raw values and reason."""
#     return cleaned.filter(todo("3: select rows with a reject_reason"))


# %% id=split-sales role=task
def accepted_sales(cleaned: DataFrame) -> DataFrame:
    """Keep parsed sales with no rejection reason, including keys absent from the lookup."""
    return cleaned.filter(F.col("reject_reason").isNull())


def rejected_sales(cleaned: DataFrame) -> DataFrame:
    """Keep invalid sales and their original values for diagnosis."""
    return cleaned.filter(F.col("reject_reason").isNotNull())


# %% id=inspect-rejected
accepted = accepted_sales(cleaned)
rejected = rejected_sales(cleaned)
rejected.select("sale_id", "amount_raw", "sold_at_raw", "reject_reason").orderBy("sale_id").show(
    truncate=False
)


# %% [markdown] id=validation-check-label
# ### Check
#
# Reconcile all eight input rows. Check which rows survive, not just how many.


# %% id=check-validation role=check
check.validation(raw, accepted, rejected)


# %% [markdown] id=hints-3 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# Use the tolerant parsing functions named in the task. Test parsed values for null.
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# A chained `when` without an `otherwise` produces null when none of its conditions matches. Filter that column with `isNull()` or `isNotNull()`.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-3). [Worked solution]({{solution}}.ipynb#exercise-3) — open it separately when you are ready to compare.


# %% [markdown] id=validation-depth depth=zoom
# ### Parseable does not always mean valid
#
# Our contract is intentionally small. It does not, for example, reject a negative amount: refunds might be legitimate. A real pipeline needs an explicit business decision about that.
#
# Keep `amount_raw` and `sold_at_raw` alongside parsed columns so a reject can be explained. Spark null checks use `isNull()`/`isNotNull()`, not Python's `is None`. The [parsing experiment](#extension-schemas) adds malformed and missing keys/timestamps without changing the main fixture.


# %% [markdown] id=parsing-zoom depth=zoom
# ### Your code — build the parsing expressions
#
# Create a separate `parsed_preview` with `sale_id`, parsed `amount` as `DECIMAL(12, 2)`, and parsed `sold_at` using `yyyy-MM-dd HH:mm:ss`. Use tolerant parsing so invalid input becomes null. Compare it with the supplied cleaner without changing that function.


# %% [starter] id=parsing-preview-starter replaces=parsing-preview depth=zoom
# parsed_preview = raw.select(
#     "sale_id",
#     todo("Parse amount_raw as a decimal without failing on invalid values").alias("amount"),
#     todo("Parse sold_at_raw with the given timestamp pattern").alias("sold_at"),
# )


# %% id=parsing-preview role=task depth=zoom
parsed_preview = raw.select(
    "sale_id",
    F.expr("try_cast(amount_raw AS DECIMAL(12, 2))").alias("amount"),
    F.try_to_timestamp("sold_at_raw", F.lit("yyyy-MM-dd HH:mm:ss")).alias("sold_at"),
)
parsed_preview.orderBy("sale_id").show()


# %% id=check-parsing-preview role=check depth=zoom
check.same_rows(cleaned.select("sale_id", "amount", "sold_at"), parsed_preview)


# %% [markdown] id=parsing-hint role=hint depth=zoom
# <details><summary>Hint for the parsing expressions</summary>
#
# Use `F.expr` with SQL `try_cast` for the decimal and `F.try_to_timestamp` with `F.lit` for the timestamp pattern. Both expressions should preserve a row even when parsing fails.
#
# </details>


# %% [markdown] id=exercise-4 role=prompt
# ---
# <a id="exercise-4"></a>
# ## Exercise 4 — Join and aggregate
#
# **What could make this report lose sales or count them twice?**
#
# Core budget: about 10 minutes.
#
# Retain every accepted sale, even without a product match. Label a missing category `unmapped` (our reporting policy). Build one report row per category, with `sales` as a row count and `total` as the sum of amount.
#
# Implement `enrich_sales` and `category_totals`; they will also be used for the stream.


# %% [markdown] id=lookup-label
# ### Supplied — check the lookup first
#
# One category per product key is required. Duplicate lookup keys would multiply sales rows.


# %% id=lookup-check role=check
check.lookup(products)


# %% [markdown] id=join-label
# ### Your code — enrich the sales


# %% [starter] id=enrich-sales-guided replaces=enrich-sales
# def enrich_sales(accepted: DataFrame, products: DataFrame) -> DataFrame:
#     """Retain sales and add their category where available."""
#     return (
#         accepted.join(products, on="product_id", how=todo("4: choose the join type"))
#         .withColumn("category", F.coalesce("category", F.lit("unmapped")))
#         .select("sale_id", "product_id", "amount", "sold_at", "category")
#     )


# %% id=enrich-sales role=task
def enrich_sales(accepted: DataFrame, products: DataFrame) -> DataFrame:
    """Join each accepted sale to its category, retaining unmatched sales as unmapped.

    Products must have one row per key; the notebook checks that contract.
    """
    return (
        accepted.join(products, on="product_id", how="left")
        .withColumn("category", F.coalesce("category", F.lit("unmapped")))
        .select("sale_id", "product_id", "amount", "sold_at", "category")
    )


# %% [markdown] id=aggregate-label
# ### Your code — the category report


# %% [starter] id=category-totals-guided replaces=category-totals
# def category_totals(enriched: DataFrame) -> DataFrame:
#     """Produce one row per category with sales and total columns."""
#     return enriched.groupBy(todo("4: grouping column")).agg(
#         todo("4: row-count expression").alias("sales"),
#         todo("4: amount-sum expression").alias("total"),
#     )


# %% id=category-totals role=task
def category_totals(enriched: DataFrame) -> DataFrame:
    """Count sales and sum decimal amounts into one row per report category."""
    return enriched.groupBy("category").agg(
        F.count("*").alias("sales"), F.sum("amount").alias("total")
    )


# %% id=show-report
enriched = enrich_sales(accepted, products)
report = category_totals(enriched)
report.orderBy("category").show()


# %% [markdown] id=report-check-label
# ### Check
#
# | category | sales | total |
# |---|---:|---:|
# | books | 3 | 50.00 |
# | games | 1 | 40.00 |
# | unmapped | 1 | 10.00 |
#
# Five accepted sales must still total 100.00. Explain the `unmapped` row in your own words.


# %% id=check-report role=check
check.report(enriched, report)


# %% [markdown] id=inner-prompt role=prompt depth=zoom
# ### Compare — without changing the working pipeline
#
# Build a separate `inner_sales` DataFrame using an inner join. Inspect its count and total. Which sale was lost? Keep `enriched` and your reusable function unchanged.


# %% [starter] id=inner-comparison-starter replaces=inner-comparison depth=zoom
# inner_sales = todo("4: a separate inner-join comparison")
# inner_sales.agg(F.count("*").alias("sales"), F.sum("amount").alias("total")).show()
# check.inner_join(inner_sales)


# %% id=inner-comparison role=task depth=zoom
inner_sales = accepted.join(products, on="product_id", how="inner")
inner_sales.agg(F.count("*").alias("sales"), F.sum("amount").alias("total")).show()
check.inner_join(inner_sales)


# %% [markdown] id=hints-4 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# Which join preserves rows from the left side when a key has no right-hand match?
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# Use a row count, not a count of nullable category values. `agg` can receive multiple expressions; give them the output names in the task.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-4). [Worked solution]({{solution}}.ipynb#exercise-4) — open it separately when you are ready to compare.


# %% [markdown] id=join-depth depth=zoom
# ### Keep track of what one row means
#
# Before aggregation, a row is an accepted sale. After grouping, a row is a category summary. `unmapped` is a reporting choice, not a join keyword. Normalising keys fixes spelling; it does not invent a missing M1 product.
#
# Explore [semi/anti joins and duplicate lookup keys](#extension-joins) or [a daily report](#extension-daily) after the core. Use separate variables for these experiments so the stream keeps its original lookup.


# %% [markdown] id=exercise-5 role=prompt
# ---
# <a id="exercise-5"></a>
# ## Exercise 5 — Inspect and save the report
#
# **What work have we described, and how can we check the saved result?**
#
# Core budget: about 5 minutes.
#
# Save the category report and rejected rows to the supplied fresh paths. Read the report back as `saved_report` and verify its values. The write/read steps are supplied for the core. Explain which operations actually execute work; the optional section investigates the physical plan.


# %% [markdown] id=plan-label role=response depth=zoom
# ### Inspect the plan
#
# Run the next cell. Find the join strategy and any `Exchange` operators shown. Explain which earlier operations they relate to. Exact operators can vary; eight rows on a laptop are not a performance benchmark.
#
# Your observations: …


# %% id=plan depth=zoom
report.explain(mode="formatted")


# %% id=save-paths
REPORT_PATH = spark_path(RUN_ROOT / "report")
REJECTED_PATH = spark_path(RUN_ROOT / "rejected")


# %% [markdown] id=save-label
# ### Supplied — write, then read back
#
# Use the default `errorifexists` mode to protect existing outputs. Run the write cell once; after a successful write, rerun just the read/check cells.


# %% id=write-report role=supplied
report.write.mode("errorifexists").parquet(REPORT_PATH)
rejected.write.mode("errorifexists").parquet(REJECTED_PATH)


# %% id=read-report role=supplied
saved_report = spark.read.parquet(REPORT_PATH)


# %% [markdown] id=save-check-label
# ### Check — supplied
#
# The saved values must match your in-memory report, and all three rejected rows must be saved.


# %% id=check-saved role=check
check.saved(report, saved_report, spark.read.parquet(REJECTED_PATH))
saved_report.orderBy("category").show()


# %% [markdown] id=hints-5 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# The DataFrame writer belongs to `.write`; the batch reader belongs to `spark.read`.
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# Writing is an action. The Python call returns None; the files are its side effect. Keep writes separate from read-back checks.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-5). [Worked solution]({{solution}}.ipynb#exercise-5) — open it separately when you are ready to compare.


# %% [markdown] id=plan-depth depth=zoom
# ### Small checks, deliberate actions
#
# Our helpers use `collect()` and counts on a tiny fixture to make mistakes visible. Do not copy repeated whole-dataset checks into a large production job without considering their cost. A formatted plan explains planned work; it does not prove runtime performance.
#
# The [repeated-work experiment](#extension-plans) compares plans and explores caching without making timing claims.


# %% [markdown] id=exercise-6 role=prompt
# ---
# <a id="exercise-6"></a>
# ## Exercise 6 — Process arriving files
#
# **Which parts change when the input keeps arriving?**
#
# Core budget: about 10 minutes.
#
# Read the initially empty `INCOMING` directory as a stream with `raw.schema`. Apply your existing functions in the same order. Keep `products` as the static lookup.
#
# Start a named memory sink for the changing aggregate. The supplied Complete mode publishes the whole current report. Paths, query name and trigger are supplied.


# %% [markdown] id=stream-reader-label
# ### Your code — change the reader, reuse your transformations


# %% [starter] id=stream-reader-guided replaces=stream-reader
# stream_raw = todo("6: use spark.readStream, raw.schema and spark_path(INCOMING)")
# stream_cleaned = clean_sales(stream_raw)
# stream_accepted = accepted_sales(stream_cleaned)
# stream_enriched = enrich_sales(stream_accepted, products)
# stream_report = category_totals(stream_enriched)


# %% id=stream-reader role=task
stream_raw = spark.readStream.schema(raw.schema).parquet(spark_path(INCOMING))
stream_cleaned = clean_sales(stream_raw)
stream_accepted = accepted_sales(stream_cleaned)
stream_enriched = enrich_sales(stream_accepted, products)
stream_report = category_totals(stream_enriched)


# %% id=stream-description role=check
print("Batch:", report.isStreaming, "Stream:", stream_report.isStreaming)
assert stream_report.isStreaming, "Use the streaming reader in Exercise 6."


# %% [markdown] id=stream-writer-label
# ### Your code — start the query
#
# A streaming DataFrame describes the computation; `start()` returns a running query. Do not call `show()` directly on the streaming DataFrame. We inspect the bounded memory table after processing each arrival.
#
# The memory sink is for this classroom demonstration, not durable output. The two-second trigger is a schedule, not a latency guarantee. Keep this writer configuration unchanged for Exercise 7.


# %% id=stream-paths
TABLE_NAME = "sales_" + uuid4().hex[:10]
CHECKPOINT_PATH = spark_path(RUN_ROOT / "report-checkpoint")


# %% [starter] id=stream-writer-guided replaces=stream-writer
# writer = (
#     stream_report.writeStream.format("memory")
#     .queryName(TABLE_NAME)
#     .outputMode("complete")
#     .option("checkpointLocation", CHECKPOINT_PATH)
#     .trigger(processingTime="2 seconds")
# )
# query = todo("6: start the writer")


# %% id=stream-writer role=task
writer = (
    stream_report.writeStream.format("memory")
    .queryName(TABLE_NAME)
    .outputMode("complete")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .trigger(processingTime="2 seconds")
)
query = writer.start()


# %% [markdown] id=arrival-one-label
# ### Supplied — first arrival
#
# Run this cell once. The helper publishes completed files and refuses duplicates. `processAllAvailable()` waits for the finite input in this demonstration; the query keeps running afterwards.
#
# After arrival 01: two accepted sales, total 65.00.


# %% id=arrival-one
assert query.isActive
publish_arrival(DATA_ROOT, INCOMING, 1)
query.processAllAvailable()


# %% id=check-arrival-one role=check
spark.table(TABLE_NAME).orderBy("category").show()
check.arrival(spark.table(TABLE_NAME), 1)
print("Query active:", query.isActive)


# %% [markdown] id=arrival-two-label role=response
# ### Predict, then publish the second arrival
#
# Arrival 02 contains s3, s4 and s6. How many should enter the report? Predict its total before running.
#
# Your prediction: …


# %% id=arrival-two
publish_arrival(DATA_ROOT, INCOMING, 2)
query.processAllAvailable()


# %% id=check-arrival-two role=check
spark.table(TABLE_NAME).orderBy("category").show()
check.arrival(spark.table(TABLE_NAME), 2)


# %% [markdown] id=hints-6 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# The reader changes, but cleaning, filtering, the static lookup join and aggregation still use your functions.
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# Output modes describe emitted result rows. The memory table should contain every current category total after an update.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-6). [Worked solution]({{solution}}.ipynb#exercise-6) — open it separately when you are ready to compare.


# %% [markdown] id=stream-depth depth=zoom
# ### Three different objects
#
# - `stream_report`: an unbounded DataFrame description.
# - `writer`: output configuration, including the checkpoint and query name.
# - `query`: the active execution, with `isActive`, `lastProgress` and `stop()`.
#
# `spark.table(TABLE_NAME)` reads the current bounded debugging result. A file arrival is not a promise of one micro-batch; checks run after the available input has been processed. Keep the static lookup and transformation definitions unchanged while the query runs.


# %% [markdown] id=stream-progress-prompt role=response depth=zoom
# ### Inspect a completed batch
#
# Run the supplied inspection cell. Which object is a description, which configures output, and which is running? Find the batch ID and the number of input rows in `lastProgress`. The latest completed batch may contain no new rows; a file is not a promised batch boundary.
#
# Your observations: …


# %% id=stream-progress depth=zoom
print("Streaming DataFrame:", stream_report.isStreaming)
print("Query active:", query.isActive)
progress = query.lastProgress
print("Last completed batch:", progress["batchId"], "input rows:", progress["numInputRows"])
print("Source descriptions:", [item["description"] for item in progress["sources"]])


# %% [markdown] id=exercise-7 role=prompt
# ---
# <a id="exercise-7"></a>
# ## Exercise 7 — Resume from a checkpoint
#
# **Will Spark count the first two arrivals again?**
#
# Core budget: about 5 minutes.
#
# Exercise 6 stopped the query. This notebook reconstructs its writer from your saved functions and the same input/checkpoint. Start it in this new session. Publish arrival 03 using the supplied cell. Compare the final stream report with the batch report.
#
# This demonstrates an orderly restart in the same environment. It does not test an arbitrary crash, and it does not turn the memory sink into durable storage.


# %% [markdown] id=restart-prediction role=response
# ### Your prediction
#
# What should the final count and total be? What does the checkpoint need to remember?
#
# Your answer: …


# %% [markdown] id=restart-label
# ### Supplied — restart the query
#
# The restart is supplied. Predict its result first, then run it. Do not create a new checkpoint here.


# %% id=restart-query role=supplied
query.stop()
assert not query.isActive
query = writer.start()


# %% [markdown] id=arrival-three-label
# ### Supplied — final arrival
#
# Run once, then use the separate check cell to inspect the result.


# %% id=arrival-three
publish_arrival(DATA_ROOT, INCOMING, 3)
query.processAllAvailable()


# %% id=check-final-stream role=check
final_stream_report = spark.table(TABLE_NAME)
final_stream_report.orderBy("category").show()
check.arrival(final_stream_report, 3)
check.same_report(report, final_stream_report)
query.stop()
print("Batch and stream agree; query stopped.")


# %% [markdown] id=hints-7 role=hint
# <details>
# <summary>Need a nudge? Hint 1</summary>
#
# Keep the saved input directory, checkpoint and writer configuration from Exercise 6.
#
# </details>
#
# <details>
# <summary>A little more help: Hint 2</summary>
#
# Exercise 6 stopped its query. Use the reconstructed writer to start execution again. A fresh checkpoint would be a new query history.
#
# </details>
#
# If you need to catch up during class, use the explicit [recovery step](RECOVERY.md#exercise-7). [Worked solution]({{solution}}.ipynb#exercise-7) — open it separately when you are ready to compare.


# %% [markdown] id=core-finish role=response
# ## The core lab is complete
#
# You have inspected and cleaned the inputs, kept rejects explainable, preserved unmatched sales, checked the saved report, and reused the transformations in a restarted stream.
#
# Before finishing, explain these three observations to a partner (or write your own notes):
#
# 1. Why does s4 stay in the report while s6 does not?
# 2. Which parts of your code changed for streaming?
# 3. Why did the restart preserve the final total rather than repeat earlier input?
#
# Your notes: …
#
# Run [Save and finish](#finish) when ready. The deeper investigations are optional and use the same saved work. Reserve time for catching up, discussion and cleanup.


# %% [markdown] id=restart-depth role=response depth=zoom
# ### Inspect the checkpoint directory
#
# The query has stopped. List the checkpoint folders below without changing them. Offset/commit logs track progress; a stateful aggregation also has saved state.
#
# What would Spark lose if we deleted this checkpoint? Why is a fresh checkpoint a new query history rather than a continuation? Record your explanation. The separate fresh-checkpoint investigation lets you test that comparison after finishing this notebook.
#
# Your explanation: …


# %% id=checkpoint-inspection depth=zoom
print(
    "Checkpoint entries:",
    sorted(item.name for item in Path(CHECKPOINT_PATH).iterdir() if not item.name.startswith(".")),
)


# %% [markdown] id=extensions
# # Deeper investigations
#
# These independent notebooks use separate experiment variables and the same saved learner functions. They do not change the core pipeline.


# %% [markdown] id=extension-schemas role=prompt
# ---
# <a id="extension-schemas"></a>
# ## Schemas and parsing
#
# Read `data/extras/sales.csv` with its header and `raw.schema` into `csv_sales`. Compare its values and schema with Parquet. Would declaring `amount_raw` as a string reject `oops`?
#
# Then read `data/extras/invalid_sales.csv` with that same schema into `extra_raw`. Apply your `clean_sales` and inspect the reasons. These extra rows are separate from the eight core inputs.


# %% [starter] id=csv-experiment-starter replaces=csv-experiment
# csv_sales = todo("Read the CSV with header=True and raw.schema")
# extra_raw = todo("Read the separate invalid-sales CSV with the same schema")
# extra_cleaned = todo("Apply your cleaning function to the extra fixture")


# %% id=csv-experiment role=task
csv_sales = (
    spark.read.option("header", True)
    .schema(raw.schema)
    .csv(spark_path(DATA_ROOT / "extras/sales.csv"))
)
extra_raw = (
    spark.read.option("header", True)
    .schema(raw.schema)
    .csv(spark_path(DATA_ROOT / "extras/invalid_sales.csv"))
)
extra_cleaned = clean_sales(extra_raw)
extra_cleaned.select("sale_id", "reject_reason").show(truncate=False)


# %% id=check-csv role=check
check.same_rows(raw, csv_sales)
check.extra_rejects(extra_cleaned)


# %% [markdown] id=csv-hint role=hint
# <details><summary>Hint</summary>
#
# Use `spark.read.option(...).schema(...).csv(...)`. A declared storage type and a business validation rule are different things.
#
# </details>


# %% [markdown] id=extension-tags role=prompt
# ---
# <a id="extension-tags"></a>
# ## Reshaping product tags
#
# Read the supplied product-tags CSV. Split `tags_raw` on the literal `|`, explode it into one `tag` per row, and keep `product_id` and `tag` as `product_tags`. Create `distinct_tags` too.
#
# Expected: six product/tag associations and five distinct tags. Explain what one output row means. Do not join this result into the sales report and sum amounts without deciding how multi-tag sales should be attributed.


# %% id=tag-input
tag_input = (
    spark.read.option("header", True)
    .schema("product_id STRING, tags_raw STRING")
    .csv(spark_path(DATA_ROOT / "extras/product_tags.csv"))
)
tag_input.show(truncate=False)


# %% [starter] id=tag-experiment-starter replaces=tag-experiment
# product_tags = todo("Split the tags, explode the array, and select product_id plus tag")
# distinct_tags = todo("Select distinct tag values")


# %% id=tag-experiment role=task
product_tags = tag_input.select("product_id", F.explode(F.split("tags_raw", r"\|")).alias("tag"))
distinct_tags = product_tags.select("tag").distinct()
product_tags.orderBy("product_id", "tag").show()


# %% id=check-tags role=check
check.tags(product_tags, distinct_tags)


# %% [markdown] id=tag-hint role=hint
# <details><summary>Hint</summary>
#
# `split` accepts a regular expression: escape the pipe so it means a literal separator. `explode` changes row grain from product to product/tag association.
#
# </details>


# %% [markdown] id=extension-joins role=prompt
# ---
# <a id="extension-joins"></a>
# ## Investigating joins
#
# Use an anti join to find accepted sales without a product, and a semi join to find those with one. Call them `unmatched` and `matched`.
#
# Then duplicate the B1 lookup row in a separate `duplicate_products` DataFrame. Make an unchecked left join called `multiplied`. Inspect its count and amount sum. Why does the lookup validation matter? Do not replace `products`.


# %% [starter] id=join-experiment-starter replaces=join-experiment
# unmatched = todo("Find accepted sales with no product match")
# matched = todo("Find accepted sales with a product match, retaining only sales columns")
# duplicate_products = todo("Add one copy of the B1 lookup row, keeping products unchanged")
# multiplied = todo("Join accepted to the duplicate lookup without applying the lookup check")


# %% id=join-experiment role=task
unmatched = accepted.join(products, on="product_id", how="left_anti")
matched = accepted.join(products, on="product_id", how="left_semi")
duplicate_products = products.unionByName(products.filter(F.col("product_id") == "B1"))
multiplied = accepted.join(duplicate_products, on="product_id", how="left")
unmatched.select("sale_id", "product_id").show()
multiplied.agg(F.count("*").alias("sales"), F.sum("amount").alias("total")).show()


# %% id=check-join-experiment role=check
check.join_experiment(unmatched, matched, multiplied)
check.lookup(products)


# %% [markdown] id=join-hint role=hint
# <details><summary>Hint</summary>
#
# Use `left_anti` and `left_semi` to test match existence. `unionByName` can deliberately add a duplicate. The extra matches multiply rows before aggregation.
#
# </details>


# %% [markdown] id=extension-daily role=prompt
# ---
# <a id="extension-daily"></a>
# ## A daily report
#
# Use `enriched` to produce `daily`: add `sale_date` from `sold_at`, group by date and category, and sum amounts as `total`. Also calculate `largest_sale` with a suitable aggregate.
#
# You should have four date/category rows whose totals still sum to 100.00. Explain how `largest_sale` differs from `total`.


# %% [starter] id=daily-experiment-starter replaces=daily-experiment
# daily = todo("Group by date and category; calculate total and largest_sale")


# %% id=daily-experiment role=task
daily = (
    enriched.withColumn("sale_date", F.to_date("sold_at"))
    .groupBy("sale_date", "category")
    .agg(F.sum("amount").alias("total"), F.max("amount").alias("largest_sale"))
)
daily.orderBy("sale_date", "category").show()


# %% id=check-daily role=check
check.daily(daily)


# %% [markdown] id=daily-hint role=hint
# <details><summary>Hint</summary>
#
# Convert the timestamp with `to_date` before grouping. Each aggregate answers a different question about the sales in that group.
#
# </details>


# %% [markdown] id=extension-plans role=prompt
# ---
# <a id="extension-plans"></a>
# ## Plans and repeated work
#
# Inspect formatted plans for a projection, the enriched sales and the category report. Where does the work expand?
#
# Make `cached_report = report.cache()`, request its rows, then inspect its plan. Finally release it with `unpersist()`. Compare values before and after. Do not use timings from this tiny fixture as evidence of a speedup.


# %% [starter] id=plan-experiment-starter replaces=plan-experiment
# todo("Inspect the three plans, then cache, materialise, check and unpersist the report")


# %% id=plan-experiment role=task
raw.select("product_id").explain(mode="formatted")
enriched.explain(mode="formatted")
report.explain(mode="formatted")
cached_report = report.cache()
try:
    cached_report.show()
    cached_report.explain(mode="formatted")
    check.same_report(report, cached_report)
finally:
    cached_report.unpersist()


# %% id=check-cache role=check
assert not report.is_cached, "Release the cached report before continuing."


# %% [markdown] id=plan-hint role=hint
# <details><summary>Hint</summary>
#
# `cache()` requests persistence. An action materialises data; the request alone does not. Use `try/finally` to release persistence even if inspection fails.
#
# </details>


# %% [markdown] id=extension-output role=prompt
# ---
# <a id="extension-output"></a>
# ## Persist streaming output
#
# Use the existing `stream_enriched` (accepted sale rows, before aggregation) to start a separate Append-mode Parquet query as `file_query`. Supply the provided new checkpoint and output path, use `availableNow=True`, and start it.
#
# This query processes the three files already present, then stops. Read its output as `stored_rows`. Verify five distinct sale IDs and a report equal to the batch result. The aggregate memory sink remains separate.


# %% id=file-paths
ROWS_CHECKPOINT = spark_path(RUN_ROOT / "rows-checkpoint")
ROWS_OUTPUT = spark_path(RUN_ROOT / "streamed-sales")


# %% [starter] id=output-experiment-starter replaces=output-experiment
# file_query = todo("Configure and start the independent Append/Parquet/AvailableNow query")


# %% id=output-experiment role=task
file_query = (
    stream_enriched.writeStream.format("parquet")
    .outputMode("append")
    .option("checkpointLocation", ROWS_CHECKPOINT)
    .trigger(availableNow=True)
    .start(ROWS_OUTPUT)
)


# %% id=await-files
finish_query(file_query)


# %% [starter] id=read-stream-output-starter replaces=read-stream-output
# stored_rows = todo("Read the completed Parquet output")


# %% id=read-stream-output role=task
stored_rows = spark.read.parquet(ROWS_OUTPUT)


# %% id=check-stream-output role=check
check.stored_rows(stored_rows)
check.same_report(report, category_totals(stored_rows))


# %% [markdown] id=output-hint role=hint
# <details><summary>Hint</summary>
#
# Start from `.writeStream` on the accepted enriched rows. Append-mode files contain new rows, not successive whole-report snapshots. Use the supplied bounded waiting helper.
#
# </details>


# %% [markdown] id=extension-checkpoint role=prompt
# ---
# <a id="extension-checkpoint"></a>
# ## Compare with a fresh checkpoint
#
# Start an independent Complete-mode memory query on `stream_report` using the supplied new name and checkpoint. Call it `fresh_query`. All three files are already in the input directory.
#
# Predict its final total. Does starting a fresh aggregate necessarily double the previous aggregate? The supplied check waits, compares and stops this independent query.


# %% id=fresh-paths
FRESH_TABLE = "fresh_" + uuid4().hex[:10]
FRESH_CHECKPOINT = spark_path(RUN_ROOT / "fresh-checkpoint")


# %% [starter] id=fresh-query-starter replaces=fresh-query
# fresh_query = todo("Start an independent memory query with a fresh checkpoint and table")


# %% id=fresh-query role=task
fresh_query = (
    stream_report.writeStream.format("memory")
    .queryName(FRESH_TABLE)
    .outputMode("complete")
    .option("checkpointLocation", FRESH_CHECKPOINT)
    .trigger(availableNow=True)
    .start()
)


# %% id=check-fresh-query role=check
finish_query(fresh_query)
check.same_report(report, spark.table(FRESH_TABLE))
spark.table(FRESH_TABLE).orderBy("category").show()


# %% [markdown] id=checkpoint-hint role=hint
# <details><summary>Hint</summary>
#
# A fresh checkpoint has no saved progress or aggregate state. It processes available files into its own new result. Whether an external sink would duplicate output is a separate question.
#
# </details>


# %% [markdown] id=cleanup
# ---
# <a id="cleanup"></a>
# ## Finish — supplied cleanup
#
# Run this cell even if you stop early or skip experiments. It stops this lab session's active queries and Spark, leaving your outputs and checkpoints intact. On a kernel restart, rerun setup and the earlier exercise cells before continuing.
#
# Keep your notebook edits for later. Compare with the separate [worked solutions]({{solution}}.ipynb) after attempting the tasks. For AWS Glue, the same transformation functions will be combined with different storage and runtime setup.


# %% id=cleanup-code
for active_query in spark.streams.active:
    active_query.stop()
spark.stop()
print("Lab session stopped. Your files remain in", RUN_ROOT)
