"""Small, observable correctness checks for the workshop's deliberately tiny fixtures."""

from datetime import date
from decimal import Decimal
from typing import NoReturn

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

EXPECTED = {
    "books": (3, Decimal("50.00")),
    "games": (1, Decimal("40.00")),
    "unmapped": (1, Decimal("10.00")),
}
RAW_COLUMNS = {"sale_id", "product_id", "amount_raw", "sold_at_raw"}


def todo(task: str) -> NoReturn:
    """Stop an unfinished starter cell without pretending that the exercise succeeded."""
    raise NotImplementedError(f"Your task: {task}. Replace this todo(...) call with your code.")


def snapshot(frame: DataFrame) -> dict[str, tuple[int, Decimal]]:
    """Collect a tiny category report while rejecting duplicate result categories."""
    rows = frame.select("category", "sales", "total").collect()
    result = {row.category: (row.sales, row.total) for row in rows}
    assert len(result) == len(rows), "The report should have one row per category."
    return result


def ids(frame: DataFrame) -> set[str]:
    """Return sale IDs for the tiny fixture; row counts are checked separately."""
    return {row.sale_id for row in frame.select("sale_id").collect()}


def inputs(raw: DataFrame, products: DataFrame) -> None:
    """Check the prepared input sizes and untouched raw column names."""
    assert raw.count() == 8, "Read the complete sales.parquet dataset: eight rows."
    assert products.count() == 3, "Read products.parquet: three lookup rows."
    assert set(raw.columns) == RAW_COLUMNS, "Keep all four original sales columns."
    print("Input check passed: eight sales and three product rows.")


def keys(raw: DataFrame, products: DataFrame, product_key) -> None:
    """Check both the learner's expression and the normalised lookup."""
    cleaned = {
        row.sale_id: row.key
        for row in raw.select("sale_id", product_key(F.col("product_id")).alias("key")).collect()
    }
    assert cleaned["s1"] == "B1" and cleaned["s2"] == "G1", "Trim spaces and uppercase the keys."
    actual = {row.product_id: row.category for row in products.collect()}
    assert actual == {"B1": "books", "G1": "games", "X1": "accessories"}, (
        "Check category trimming/casing and output aliases."
    )
    assert raw.filter(F.col("sale_id") == "s1").first().product_id == " b1 ", "Keep raw unchanged."
    print("Key check passed; the original input is still available.")


def lookup(products: DataFrame) -> None:
    """Reject missing and duplicate lookup keys before the sale grain can multiply."""
    assert (
        products.filter(F.col("product_id").isNull() | (F.col("product_id") == "")).count() == 0
    ), "The lookup has a missing product key."
    assert products.groupBy("product_id").count().filter(F.col("count") > 1).count() == 0, (
        "Duplicate product keys would multiply sales rows."
    )
    print("Lookup check passed: one row per product key.")


def validation(raw: DataFrame, accepted: DataFrame, rejected: DataFrame) -> None:
    """Reconcile rows and reasons rather than accepting a coincidental count match."""
    assert raw.count() == accepted.count() + rejected.count() == 8, (
        "Every input must be accepted or rejected exactly once."
    )
    assert accepted.count() == 5 and ids(accepted) == {"s1", "s2", "s3", "s4", "s5"}, (
        "Keep s1–s5, including the valid M1 sale."
    )
    reasons = {row.sale_id: row.reject_reason for row in rejected.collect()}
    assert reasons == {
        "s6": "invalid or missing amount",
        "s7": "invalid or missing amount",
        "s8": "invalid or missing timestamp",
    }, "Check the rejected IDs and parsing reasons."
    print("Validation passed: 8 input = 5 accepted + 3 rejected; M1 is accepted.")


def report(enriched: DataFrame, result: DataFrame) -> None:
    """Require the baseline sale population and category report."""
    assert enriched.count() == 5 and ids(enriched) == {"s1", "s2", "s3", "s4", "s5"}, (
        "The join must keep all five accepted sales once."
    )
    assert snapshot(result) == EXPECTED, "Expected books 3/50.00, games 1/40.00, unmapped 1/10.00."
    print("Report check passed: five sales, total 100.00.")


def inner_join(frame: DataFrame) -> None:
    """Check the explicit comparison without changing the working left-join pipeline."""
    assert frame.count() == 4 and ids(frame) == {"s1", "s2", "s3", "s5"}, (
        "The unmatched M1 sale should be absent from the inner join."
    )
    assert frame.agg(F.sum("amount")).first()[0] == Decimal("90.00"), (
        "The inner-join amount total should be 90.00."
    )
    print("Inner join: four sales, total 90.00. Explain the missing 10.00.")


def same_report(first: DataFrame, second: DataFrame) -> None:
    """Compare report values independently of ordering or partition layout."""
    assert snapshot(first) == snapshot(second) == EXPECTED, (
        "Both reports must match the baseline category values."
    )
    print("Reports agree: five sales, total 100.00.")


def saved(original: DataFrame, reloaded: DataFrame, rejects: DataFrame) -> None:
    """Verify persisted report values and the rejected-row audit output."""
    same_report(original, reloaded)
    assert rejects.count() == 3 and ids(rejects) == {"s6", "s7", "s8"}, (
        "Save all three rejected rows too."
    )
    print("Saved report and rejected rows verified.")


def arrival(frame: DataFrame, number: int) -> None:
    """Check after a controlled file arrival without assuming a particular batch ID."""
    expected = {
        1: {"books": (1, Decimal("25.00")), "games": (1, Decimal("40.00"))},
        2: {
            "books": (2, Decimal("40.00")),
            "games": (1, Decimal("40.00")),
            "unmapped": (1, Decimal("10.00")),
        },
        3: EXPECTED,
    }[number]
    actual = snapshot(frame)
    assert actual == expected, (
        f"Arrival {number}: expected {expected}, got {actual}. Check your functions and published files."
    )
    print(
        f"Arrival {number} verified: {sum(value[0] for value in actual.values())} sales; total {sum(value[1] for value in actual.values()):.2f}."
    )


def same_rows(first: DataFrame, second: DataFrame) -> None:
    """Compare two tiny fixtures including duplicate multiplicity and column order."""
    aligned = second.select(*first.columns)
    assert first.exceptAll(aligned).count() == aligned.exceptAll(first).count() == 0, (
        "CSV and Parquet should contain the same rows."
    )
    print("CSV and Parquet values agree.")


def extra_rejects(frame: DataFrame) -> None:
    """Verify the optional parsing fixture without changing the core report."""
    actual = {row.sale_id: row.reject_reason for row in frame.collect()}
    assert actual == {
        "x1": "missing product key",
        "x2": "invalid or missing timestamp",
        "x3": None,
    }, (
        "Missing keys/timestamps fail; the parseable negative amount is allowed by this lab's contract."
    )
    print("Extra parsing checks passed. Discuss whether the business would accept x3.")


def projection(raw: DataFrame, changed: DataFrame) -> None:
    """Check that a derived projection preserved the original DataFrame description."""
    assert raw.count() == changed.count() == 8, "This projection should retain eight rows."
    assert set(raw.columns) == RAW_COLUMNS, "Keep the original schema available."
    assert set(changed.columns) == {"sale_id", "product_id", "source_amount", "clean_key"}, (
        "Check the added, renamed and dropped columns."
    )
    print("Projection check passed; raw is unchanged.")


def tags(associations: DataFrame, distinct_tags: DataFrame) -> None:
    """Require the actual tag associations, not just a matching row count."""
    actual = {(row.product_id, row.tag) for row in associations.collect()}
    expected = {
        ("B1", "books"),
        ("B1", "reading"),
        ("G1", "games"),
        ("G1", "gifts"),
        ("X1", "accessories"),
        ("X1", "gifts"),
    }
    assert associations.count() == 6 and actual == expected, (
        "Expected six product/tag associations; split on a literal pipe."
    )
    assert distinct_tags.count() == 5 and {row.tag for row in distinct_tags.collect()} == {
        tag for _, tag in expected
    }, "There should be five distinct tags."
    print("Tags: six associations, five distinct values.")


def join_experiment(unmatched: DataFrame, matched: DataFrame, multiplied: DataFrame) -> None:
    """Check existence joins and the deliberate duplicate-lookup experiment."""
    assert ids(unmatched) == {"s4"} and unmatched.count() == 1, "The anti join should isolate s4."
    assert ids(matched) == {"s1", "s2", "s3", "s5"} and matched.count() == 4, (
        "The semi join should retain the four matched sales."
    )
    assert multiplied.count() == 8 and multiplied.agg(F.sum("amount")).first()[0] == Decimal(
        "150.00"
    ), "Duplicating B1 should multiply its three sales and add 50.00."
    print("Duplicate lookup demonstrated: eight joined rows, total 150.00.")


def daily(frame: DataFrame) -> None:
    """Verify each optional date/category group and its largest sale."""
    actual = {
        (row.sale_date, row.category): (row.total, row.largest_sale) for row in frame.collect()
    }
    expected = {
        (date(2026, 9, 1), "books"): (Decimal("25.00"), Decimal("25.00")),
        (date(2026, 9, 1), "games"): (Decimal("40.00"), Decimal("40.00")),
        (date(2026, 9, 2), "books"): (Decimal("25.00"), Decimal("15.00")),
        (date(2026, 9, 2), "unmapped"): (Decimal("10.00"), Decimal("10.00")),
    }
    assert frame.count() == 4 and actual == expected, (
        "Check dates, categories and the difference between sum and maximum."
    )
    print("Daily report verified: four groups, total 100.00.")


def stored_rows(frame: DataFrame) -> None:
    """Require one persisted row for each accepted sale."""
    assert frame.count() == 5 and ids(frame) == {"s1", "s2", "s3", "s4", "s5"}, (
        "Persist exactly the five accepted sale rows."
    )
    print("Stored streaming rows verified: five distinct accepted sales.")
