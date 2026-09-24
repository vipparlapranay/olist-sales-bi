"""
Unit tests for the data quality checks.

A check that never fails is worthless, so each test deliberately feeds in broken data
and asserts that the check catches it. That's the part people forget.
"""
from __future__ import annotations

import pandas as pd

from olist import validate


def test_not_null_catches_missing_values():
    df = pd.DataFrame({"order_id": ["a", None, "c"]})
    result = validate.check_not_null(df, "orders", ["order_id"])[0]
    assert not result.passed
    assert result.bad_rows == 1
    assert result.status == "FAIL"  # critical by default


def test_not_null_passes_on_clean_data():
    df = pd.DataFrame({"order_id": ["a", "b"]})
    assert validate.check_not_null(df, "orders", ["order_id"])[0].passed


def test_unique_key_catches_duplicates():
    df = pd.DataFrame({"order_id": ["a", "a", "b"], "item": [1, 1, 1]})
    result = validate.check_unique_key(df, "items", ["order_id", "item"])
    assert not result.passed
    assert result.bad_rows == 1


def test_warning_severity_reports_warn_not_fail():
    """Known quirks should warn, not stop the pipeline."""
    df = pd.DataFrame({"review_id": ["r1", "r1"]})
    result = validate.check_unique_key(df, "reviews", ["review_id"], validate.WARNING)
    assert not result.passed
    assert result.status == "WARN"


def test_allowed_values_flags_unexpected_category():
    df = pd.DataFrame({"order_status": ["delivered", "teleported"]})
    result = validate.check_allowed_values(df, "orders", "order_status",
                                           {"delivered", "shipped"})
    assert not result.passed
    assert "teleported" in result.detail


def test_non_negative_catches_negative_price():
    df = pd.DataFrame({"price": [10.0, -5.0, 0.0]})
    result = validate.check_non_negative(df, "items", ["price"])[0]
    assert not result.passed
    assert result.bad_rows == 1


def test_referential_integrity_catches_orphans():
    child = pd.DataFrame({"order_id": ["a", "b", "ghost"]})
    parent = pd.DataFrame({"order_id": ["a", "b"]})
    result = validate.check_referential_integrity(child, parent, "items",
                                                  "order_id", "order_id")
    assert not result.passed
    assert result.bad_rows == 1


def test_date_order_catches_delivery_before_purchase():
    df = pd.DataFrame({
        "purchase": pd.to_datetime(["2018-01-10", "2018-01-01"]),
        "delivered": pd.to_datetime(["2018-01-05", "2018-01-09"]),
    })
    result = validate.check_date_order(df, "orders", "purchase", "delivered")
    assert not result.passed
    assert result.bad_rows == 1


def test_quality_score_weights_critical_higher_than_warning():
    """One critical failure should hurt more than one warning failure."""
    passing = validate.CheckResult("t", "c", validate.CRITICAL, True, 0, "")
    crit_fail = validate.CheckResult("t", "c", validate.CRITICAL, False, 1, "")
    warn_fail = validate.CheckResult("t", "c", validate.WARNING, False, 1, "")

    def score(results):
        df = pd.DataFrame([r.__dict__ | {"status": r.status} for r in results])
        return validate.quality_score(df)

    with_critical_fail = score([passing, crit_fail])
    with_warning_fail = score([passing, warn_fail])
    assert with_critical_fail < with_warning_fail


def test_quality_score_is_100_when_everything_passes():
    results = [validate.CheckResult("t", f"c{i}", validate.CRITICAL, True, 0, "")
               for i in range(3)]
    df = pd.DataFrame([r.__dict__ | {"status": r.status} for r in results])
    assert validate.quality_score(df) == 100.0
