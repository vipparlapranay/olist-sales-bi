"""
validate.py — a small data quality framework with a scorecard.

WHY THIS FILE EXISTS (and why it's a resume bullet)
--------------------------------------------------
Most portfolio projects load a CSV and start charting. Real analysts check the data
first, because a dashboard built on broken data is worse than no dashboard: it's
confidently wrong.

This module runs a set of named checks, each returning a pass/fail with a count of bad
rows, then scores the dataset out of 100 and writes docs/data_quality_report.md.
Critical failures can stop the pipeline (--strict), which is how production data
pipelines behave.

The design is deliberately simple: each check is a plain function returning a
CheckResult. That makes checks easy to unit test (see tests/test_validate.py).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from . import config, io_utils

log = logging.getLogger(__name__)

# Severity levels. CRITICAL failures mean the numbers cannot be trusted at all;
# WARNING means "known quirk of this dataset, handled downstream".
CRITICAL = "critical"
WARNING = "warning"


@dataclass
class CheckResult:
    table: str
    check: str
    severity: str
    passed: bool
    bad_rows: int
    detail: str

    @property
    def status(self) -> str:
        return "PASS" if self.passed else ("FAIL" if self.severity == CRITICAL else "WARN")


# ---------------------------------------------------------------------------
# Individual check functions. Each one answers a single question about the data.
# ---------------------------------------------------------------------------

def check_not_null(df: pd.DataFrame, table: str, columns: Iterable[str],
                   severity: str = CRITICAL) -> list[CheckResult]:
    """Every listed column must be fully populated."""
    results = []
    for col in columns:
        bad = int(df[col].isna().sum())
        results.append(CheckResult(
            table, f"not_null({col})", severity, bad == 0, bad,
            f"{bad:,} null values" if bad else "no nulls",
        ))
    return results


def check_unique_key(df: pd.DataFrame, table: str, key: list[str],
                     severity: str = CRITICAL) -> CheckResult:
    """The stated primary key must identify exactly one row."""
    bad = int(df.duplicated(subset=key).sum())
    return CheckResult(
        table, f"unique_key({'+'.join(key)})", severity, bad == 0, bad,
        f"{bad:,} duplicate keys" if bad else "key is unique",
    )


def check_allowed_values(df: pd.DataFrame, table: str, column: str,
                         allowed: set[str], severity: str = WARNING) -> CheckResult:
    """Categorical columns must only contain values we know how to handle."""
    found = set(df[column].dropna().unique())
    unexpected = found - allowed
    bad = int(df[column].isin(unexpected).sum()) if unexpected else 0
    return CheckResult(
        table, f"allowed_values({column})", severity, not unexpected, bad,
        f"unexpected: {sorted(unexpected)}" if unexpected else f"{len(found)} known values",
    )


def check_non_negative(df: pd.DataFrame, table: str, columns: Iterable[str],
                       severity: str = CRITICAL) -> list[CheckResult]:
    """Money and quantities cannot be negative."""
    results = []
    for col in columns:
        bad = int((df[col] < 0).sum())
        results.append(CheckResult(
            table, f"non_negative({col})", severity, bad == 0, bad,
            f"{bad:,} negative values" if bad else "all values >= 0",
        ))
    return results


def check_referential_integrity(child: pd.DataFrame, parent: pd.DataFrame, table: str,
                                child_key: str, parent_key: str,
                                severity: str = CRITICAL) -> CheckResult:
    """Every foreign key in the child table must exist in the parent table.

    Orphan keys are the classic cause of "revenue doesn't add up": rows silently
    disappear (inner join) or produce blanks (left join) in the model.
    """
    orphans = ~child[child_key].isin(set(parent[parent_key]))
    bad = int(orphans.sum())
    return CheckResult(
        table, f"fk({child_key} -> {parent_key})", severity, bad == 0, bad,
        f"{bad:,} orphan keys" if bad else "all keys matched",
    )


def check_date_order(df: pd.DataFrame, table: str, earlier: str, later: str,
                     severity: str = WARNING) -> CheckResult:
    """Chronology check: a delivery cannot happen before the purchase."""
    both = df[[earlier, later]].dropna()
    bad = int((both[later] < both[earlier]).sum())
    return CheckResult(
        table, f"date_order({earlier} <= {later})", severity, bad == 0, bad,
        f"{bad:,} rows out of order" if bad else "chronology valid",
    )


# ---------------------------------------------------------------------------
# The suite: every check we run against the Olist dataset.
# ---------------------------------------------------------------------------

def run_all_checks(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run the full suite and return results as a DataFrame."""
    orders, items = frames["orders"], frames["items"]
    payments, reviews = frames["payments"], frames["reviews"]
    customers, products = frames["customers"], frames["products"]
    sellers = frames["sellers"]

    known_statuses = {"delivered", "shipped", "canceled", "unavailable",
                      "invoiced", "processing", "created", "approved"}

    results: list[CheckResult] = []

    # --- orders: the spine of the model
    results.append(check_unique_key(orders, "orders", ["order_id"]))
    results += check_not_null(orders, "orders", ["order_id", "customer_id", "order_status"])
    results.append(check_allowed_values(orders, "orders", "order_status", known_statuses))
    results.append(check_date_order(orders, "orders",
                                    "order_purchase_timestamp", "order_delivered_customer_date"))
    # Undelivered orders legitimately have no delivery date, so this is a WARNING.
    results += check_not_null(orders, "orders", ["order_delivered_customer_date"], WARNING)

    # --- order items: where revenue lives
    results.append(check_unique_key(items, "items", ["order_id", "order_item_id"]))
    results += check_non_negative(items, "items", ["price", "freight_value"])
    results.append(check_referential_integrity(items, orders, "items", "order_id", "order_id"))
    results.append(check_referential_integrity(items, products, "items", "product_id", "product_id"))
    results.append(check_referential_integrity(items, sellers, "items", "seller_id", "seller_id"))

    # --- payments and reviews: both are at a different grain to orders
    results.append(check_unique_key(payments, "payments", ["order_id", "payment_sequential"]))
    results += check_non_negative(payments, "payments", ["payment_value"])
    # review_id is NOT unique in this dataset. Expected quirk -> WARNING, handled in transform.
    results.append(check_unique_key(reviews, "reviews", ["review_id"], WARNING))
    results.append(check_unique_key(reviews, "reviews", ["order_id"], WARNING))
    results.append(check_allowed_values(reviews, "reviews", "review_score",
                                        {1, 2, 3, 4, 5}, CRITICAL))

    # --- dimensions
    results.append(check_unique_key(customers, "customers", ["customer_id"]))
    results.append(check_unique_key(products, "products", ["product_id"]))
    results.append(check_unique_key(sellers, "sellers", ["seller_id"]))
    results.append(check_referential_integrity(orders, customers, "orders",
                                               "customer_id", "customer_id"))

    df = pd.DataFrame([r.__dict__ | {"status": r.status} for r in results])
    return df[["table", "check", "severity", "status", "bad_rows", "detail"]]


def quality_score(results: pd.DataFrame) -> float:
    """Score the dataset out of 100.

    Critical checks are worth 3x a warning, so failing a foreign key hurts far more
    than a known quirk. The weighting is a judgement call; document it rather than
    pretending the number is objective.
    """
    weights = results["severity"].map({CRITICAL: 3.0, WARNING: 1.0})
    earned = (weights * (results["status"] == "PASS")).sum()
    return round(100 * earned / weights.sum(), 1)


def write_report(results: pd.DataFrame, score: float) -> None:
    """Write docs/data_quality_report.md — a document you can show an interviewer."""
    failed = results[results["status"] == "FAIL"]
    warned = results[results["status"] == "WARN"]

    lines = [
        "# Data quality report",
        "",
        f"**Quality score: {score} / 100**  "
        f"({(results['status'] == 'PASS').sum()} passed, {len(warned)} warnings, {len(failed)} failures "
        f"across {len(results)} checks)",
        "",
        "Critical checks are weighted 3x warnings. Warnings are known quirks of this "
        "dataset that the transform layer handles deliberately.",
        "",
        "| Table | Check | Severity | Status | Bad rows | Detail |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in results.iterrows():
        lines.append(
            f"| {r['table']} | `{r['check']}` | {r['severity']} | **{r['status']}** "
            f"| {r['bad_rows']:,} | {r['detail']} |"
        )

    lines += ["", "## How each warning is handled", "",
              "- **reviews.unique_key** — review_id repeats and some orders have several "
              "reviews. The transform keeps the latest review per order.",
              "- **orders.not_null(order_delivered_customer_date)** — undelivered orders have "
              "no delivery date. Delivery metrics only include delivered orders.",
              "- **orders.date_order** — a handful of rows have odd timestamps; they are "
              "excluded from delivery-time averages."]

    io_utils.write_markdown(lines, "data_quality_report.md")


def run(frames: dict[str, pd.DataFrame], strict: bool = False) -> tuple[pd.DataFrame, float]:
    """Entry point used by the pipeline: run checks, score, report, optionally stop."""
    results = run_all_checks(frames)
    score = quality_score(results)
    write_report(results, score)

    for _, r in results[results["status"] != "PASS"].iterrows():
        log.warning("%s %s.%s — %s", r["status"], r["table"], r["check"], r["detail"])
    log.info("data quality score: %.1f/100", score)

    failures = results[results["status"] == "FAIL"]
    if strict and not failures.empty:
        raise SystemExit(
            f"{len(failures)} critical data quality check(s) failed. "
            "See docs/data_quality_report.md"
        )
    return results, score
