"""Run the workshop preflight with ``uv run --locked check_setup.py``."""

from __future__ import annotations

import platform
import sys
import traceback
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from arrival_files import publish_arrival
from pipeline import accepted_sales, category_totals, clean_products, clean_sales, enrich_sales
from workshop_runtime import (
    DATA_ROOT,
    create_spark,
    finish_query,
    java_version,
    new_run,
    spark_path,
)

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


def worker_python(_: object) -> tuple[int, int]:
    """Report the interpreter inside a Spark Python worker rather than the driver."""
    import sys

    return sys.version_info[:2]


def check_python_worker(spark: SparkSession) -> None:
    """Verify that Spark can launch a worker using the lab's Python version."""
    actual = spark.sparkContext.parallelize([1], 1).map(worker_python).collect()
    assert actual == [(3, 12)], actual
    print("PASS: local Spark and Python worker", flush=True)


def check_parquet(spark: SparkSession, run_root: Path) -> DataFrame:
    """Read the prepared sales and verify a round trip through a fresh Parquet directory."""
    raw = spark.read.parquet(spark_path(DATA_ROOT / "sales.parquet"))
    output = spark_path(run_root / "parquet-check")
    raw.write.mode("errorifexists").parquet(output)
    assert spark.read.parquet(output).count() == 8
    print("PASS: prepared Parquet input and output", flush=True)
    return raw


def check_checkpoint_restart(
    spark: SparkSession, accepted: DataFrame, incoming: Path, run_root: Path
) -> None:
    """Process two arrivals through the same checkpoint and verify retained aggregate state."""
    table = "setup_" + run_root.name.replace("-", "_")
    writer = (
        category_totals(accepted)
        .writeStream.format("memory")
        .queryName(table)
        .outputMode("complete")
        .option("checkpointLocation", spark_path(run_root / "report-checkpoint"))
        .trigger(availableNow=True)
    )
    expectations = [
        {"books": (1, Decimal("25.00")), "games": (1, Decimal("40.00"))},
        {
            "books": (2, Decimal("40.00")),
            "games": (1, Decimal("40.00")),
            "unmapped": (1, Decimal("10.00")),
        },
    ]
    for number, expected in enumerate(expectations, 1):
        publish_arrival(DATA_ROOT, incoming, number)
        finish_query(writer.start())
        actual = {row.category: (row.sales, row.total) for row in spark.table(table).collect()}
        assert actual == expected, f"Arrival {number}: {actual}"
    print("PASS: file arrivals, aggregate state and checkpoint restart", flush=True)


def check_streaming_output(spark: SparkSession, accepted: DataFrame, run_root: Path) -> None:
    """Write accepted rows to a separate sink and check that both arrivals appear once."""
    output = spark_path(run_root / "streamed-sales")
    query = (
        accepted.writeStream.format("parquet")
        .outputMode("append")
        .option("checkpointLocation", spark_path(run_root / "rows-checkpoint"))
        .trigger(availableNow=True)
        .start(output)
    )
    finish_query(query)
    stored = spark.read.parquet(output)
    assert {row.sale_id for row in stored.select("sale_id").collect()} == {"s1", "s2", "s3", "s4"}
    assert stored.count() == 4
    print("PASS: streaming Parquet sink", flush=True)


def run_checks(spark: SparkSession, run_root: Path) -> None:
    """Exercise workers, local files, streaming recovery and output using the actual fixture."""
    check_python_worker(spark)
    raw = check_parquet(spark, run_root)
    products = clean_products(spark.read.parquet(spark_path(DATA_ROOT / "products.parquet")))
    incoming = run_root / "incoming"
    incoming.mkdir()
    rows = spark.readStream.schema(raw.schema).parquet(spark_path(incoming))
    accepted = enrich_sales(accepted_sales(clean_sales(rows)), products)
    check_checkpoint_restart(spark, accepted, incoming, run_root)
    check_streaming_output(spark, accepted, run_root)


def main() -> int:
    """Run the preflight, retain diagnostic files and stop the session even on failure."""
    run_root = new_run("setup")
    spark = None
    try:
        print(f"Platform: {platform.system()} {platform.machine()}", flush=True)
        print(f"Python: {platform.python_version()}; Java: {java_version()}", flush=True)
        spark = create_spark(run_root)
        print(f"Spark: {spark.version}", flush=True)
        run_checks(spark, run_root)
        print(
            "Setup check passed. Open notebooks/01-inspect.ipynb to begin.",
            flush=True,
        )
        return 0
    except Exception:
        traceback.print_exc()
        print(
            "\nSetup check failed. Keep this output and see TROUBLESHOOTING.md.",
            file=sys.stderr,
        )
        return 1
    finally:
        if spark is not None:
            spark.stop()
        print(f"Check files: {run_root}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
