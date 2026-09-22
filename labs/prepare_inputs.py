"""Author utility. Learners read the prepared Parquet files in the notebook.

Run with a compatible local PySpark installation. Existing outputs are preserved.
The one-partition writes package these tiny teaching fixtures; they are not a
recommendation for production file sizing.
"""

import csv
from pathlib import Path

from pyspark.sql import SparkSession

SALES = [
    ("s1", " b1 ", "25.00", "2026-09-01 09:00:00"),
    ("s2", "g1", "40.00", "2026-09-01 09:05:00"),
    ("s3", "B1", "15.00", "2026-09-02 10:00:00"),
    ("s4", "M1", "10.00", "2026-09-02 11:00:00"),
    ("s5", "B1", "10.00", "2026-09-02 12:00:00"),
    ("s6", "B1", "oops", "2026-09-02 12:05:00"),
    ("s7", "G1", None, "2026-09-02 12:10:00"),
    ("s8", "B1", "5.00", "not-a-date"),
]
SCHEMA = "sale_id STRING, product_id STRING, amount_raw STRING, sold_at_raw STRING"
PRODUCTS = [("B1", " Books "), ("G1", "GAMES"), ("X1", "accessories")]


def prepare_extras(destination: Path) -> None:
    """Write the optional CSV fixtures without replacing existing files."""
    extras = destination / "extras"
    extras.mkdir(parents=True, exist_ok=True)
    raw_columns = ["sale_id", "product_id", "amount_raw", "sold_at_raw"]
    fixtures = {
        "sales.csv": (raw_columns, SALES),
        "invalid_sales.csv": (
            raw_columns,
            [
                ("x1", " ", "5.00", "2026-09-01 09:00:00"),
                ("x2", "B1", "5.00", None),
                ("x3", "B1", "-2.00", "2026-09-01 09:00:00"),
            ],
        ),
        "product_tags.csv": (
            ["product_id", "tags_raw"],
            [
                ("B1", "books|reading"),
                ("G1", "games|gifts"),
                ("X1", "accessories|gifts"),
            ],
        ),
    }
    for name, (header, rows) in fixtures.items():
        with (extras / name).open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)


def prepare(spark: SparkSession, destination: Path) -> None:
    """Write the raw inputs and three arrivals without replacing an existing fixture."""
    destination = Path(destination)
    prepare_extras(destination)
    spark.createDataFrame(SALES, SCHEMA).coalesce(1).write.mode("errorifexists").parquet(
        str(destination / "sales.parquet")
    )
    spark.createDataFrame(PRODUCTS, "product_id STRING, category STRING").coalesce(1).write.mode(
        "errorifexists"
    ).parquet(str(destination / "products.parquet"))
    for number, indices in enumerate(((0, 1), (2, 3, 5), (4, 6, 7)), 1):
        spark.createDataFrame([SALES[i] for i in indices], SCHEMA).coalesce(1).write.mode(
            "errorifexists"
        ).parquet(str(destination / "arrivals" / f"{number:02d}"))


def main() -> None:
    """Generate the fixture with a local session and always release its resources."""
    session = SparkSession.builder.master("local[2]").appName("DCC fixtures").getOrCreate()
    try:
        session.sparkContext.setLogLevel("ERROR")
        prepare(session, Path(__file__).parent / "data")
    finally:
        session.stop()


if __name__ == "__main__":
    main()
