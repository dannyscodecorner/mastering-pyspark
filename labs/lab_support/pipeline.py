"""Chapter 08 transformations, shared by the batch and streaming exercises.

The caller supplies Spark DataFrames. This module does not create a session,
read files, execute actions, or choose a deployment environment.
"""

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F


def product_key(column: Column) -> Column:
    """Build a Spark Column expression; this is not a Python UDF."""
    return F.upper(F.trim(column))


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


def clean_products(raw: DataFrame) -> DataFrame:
    """Normalise product keys and category names while retaining the lookup row grain."""
    return raw.select(
        product_key(F.col("product_id")).alias("product_id"),
        F.lower(F.trim("category")).alias("category"),
    )


def accepted_sales(cleaned: DataFrame) -> DataFrame:
    """Keep parsed sales with no rejection reason, including keys absent from the lookup."""
    return cleaned.filter(F.col("reject_reason").isNull())


def rejected_sales(cleaned: DataFrame) -> DataFrame:
    """Keep invalid sales and their original values for diagnosis."""
    return cleaned.filter(F.col("reject_reason").isNotNull())


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
