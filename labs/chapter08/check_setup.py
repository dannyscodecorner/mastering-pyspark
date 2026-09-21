"""Run before the workshop: uv run --locked check_setup.py."""

from decimal import Decimal
import platform
import sys
import traceback

from arrival_files import publish_arrival
from pipeline import accepted_sales, category_totals, clean_products, clean_sales, enrich_sales
from workshop_runtime import DATA_ROOT, create_spark, finish_query, java_version, new_run, spark_path


def worker_python(_):
    # Exercise the worker process as well as the driver JVM.
    import sys
    return sys.version_info[:2]


def main():
    run_root = new_run("setup")
    spark = None
    try:
        print(f"Platform: {platform.system()} {platform.machine()}", flush=True)
        print(f"Python: {platform.python_version()}; Java: {java_version()}", flush=True)
        spark = create_spark(run_root)
        print(f"Spark: {spark.version}", flush=True)
        assert spark.sparkContext.parallelize([1], 1).map(worker_python).collect() == [(3, 12)]
        print("PASS: local Spark and Python worker", flush=True)

        raw = spark.read.parquet(spark_path(DATA_ROOT / "sales.parquet"))
        products = clean_products(spark.read.parquet(spark_path(DATA_ROOT / "products.parquet")))
        raw.write.mode("errorifexists").parquet(spark_path(run_root / "parquet-check"))
        assert spark.read.parquet(spark_path(run_root / "parquet-check")).count() == 8
        print("PASS: prepared Parquet input and output", flush=True)

        incoming = run_root / "incoming"
        incoming.mkdir()
        rows = spark.readStream.schema(raw.schema).parquet(spark_path(incoming))
        accepted = enrich_sales(accepted_sales(clean_sales(rows)), products)
        table = "setup_" + run_root.name.replace("-", "_")
        writer = (
            category_totals(accepted).writeStream.format("memory")
            .queryName(table).outputMode("complete")
            .option("checkpointLocation", spark_path(run_root / "report-checkpoint"))
            .trigger(availableNow=True)
        )
        for number, expected in [
            (1, {"books": (1, Decimal("25.00")), "games": (1, Decimal("40.00"))}),
            (2, {"books": (2, Decimal("40.00")), "games": (1, Decimal("40.00")), "unmapped": (1, Decimal("10.00"))}),
        ]:
            publish_arrival(DATA_ROOT, incoming, number)
            finish_query(writer.start())
            actual = {r.category: (r.sales, r.total) for r in spark.table(table).collect()}
            assert actual == expected, f"Arrival {number}: {actual}"
        print("PASS: file arrivals, aggregate state and checkpoint restart", flush=True)

        finish_query(
            accepted.writeStream.format("parquet").outputMode("append")
            .option("checkpointLocation", spark_path(run_root / "rows-checkpoint"))
            .trigger(availableNow=True).start(spark_path(run_root / "streamed-sales"))
        )
        stored = spark.read.parquet(spark_path(run_root / "streamed-sales"))
        assert {r.sale_id for r in stored.select("sale_id").collect()} == {"s1", "s2", "s3", "s4"}
        assert stored.count() == 4
        print("PASS: streaming Parquet sink", flush=True)
        print("Setup check passed. Open hands_on.py or hands-on.ipynb to begin.", flush=True)
        return 0
    except Exception:
        traceback.print_exc()
        print("\nSetup check failed. Keep this output and see README.md: Troubleshooting.", file=sys.stderr)
        return 1
    finally:
        if spark is not None:
            spark.stop()
        print(f"Check files: {run_root}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
