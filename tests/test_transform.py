"""
Unit tests for the transform layer.

WHY TEST THIS
-------------
The transform module encodes the business rules. If someone (including future you)
changes how "late" is defined, these tests fail loudly instead of the dashboard quietly
reporting the wrong number for six months.

Each test builds a tiny DataFrame by hand where the correct answer is obvious, which is
the whole point: you can verify the expected value in your head.

Run them with:   pytest
"""
from __future__ import annotations

import pandas as pd
import pytest

from olist import transform


@pytest.fixture
def orders() -> pd.DataFrame:
    """Four orders covering every case that matters."""
    return pd.DataFrame({
        "order_id": ["on_time", "late", "cancelled", "not_delivered"],
        "customer_id": ["c1", "c2", "c3", "c4"],
        "order_status": ["delivered", "delivered", "canceled", "shipped"],
        "order_purchase_timestamp": pd.to_datetime(
            ["2018-01-01", "2018-01-01", "2018-01-01", "2018-01-01"]),
        "order_approved_at": pd.to_datetime(["2018-01-01"] * 4),
        "order_delivered_carrier_date": pd.to_datetime(["2018-01-02"] * 4),
        # on_time arrives late in the evening of the promised day -> NOT late
        "order_delivered_customer_date": pd.to_datetime(
            ["2018-01-10 23:00", "2018-01-15 08:00", None, None]),
        "order_estimated_delivery_date": pd.to_datetime(["2018-01-10"] * 4),
    })


@pytest.fixture
def payments() -> pd.DataFrame:
    """One order paid in two parts — the classic grain trap."""
    return pd.DataFrame({
        "order_id": ["on_time", "on_time", "late"],
        "payment_sequential": [1, 2, 1],
        "payment_type": ["voucher", "credit_card", "credit_card"],
        "payment_installments": [1, 3, 2],
        "payment_value": [20.0, 80.0, 50.0],
    })


@pytest.fixture
def reviews() -> pd.DataFrame:
    """One order reviewed twice — the later review should win."""
    return pd.DataFrame({
        "review_id": ["r1", "r2", "r3"],
        "order_id": ["on_time", "on_time", "late"],
        "review_score": [1, 5, 2],
        "review_answer_timestamp": pd.to_datetime(
            ["2018-01-11", "2018-01-20", "2018-01-16"]),
    })


def test_payments_collapse_to_one_row_per_order(payments):
    out = transform.aggregate_payments(payments)
    assert len(out) == 2, "payments must be reduced to one row per order"
    on_time = out.set_index("order_id").loc["on_time"]
    assert on_time["payment_value"] == 100.0, "payment lines should be summed"
    assert on_time["main_payment_type"] == "credit_card", "largest payment wins"
    assert on_time["payment_lines"] == 2


def test_reviews_keep_the_latest_per_order(reviews):
    out = transform.aggregate_reviews(reviews).set_index("order_id")
    assert out.loc["on_time", "review_score"] == 5, "latest review must win, not the first"
    assert out.loc["on_time", "review_count"] == 2
    assert len(out) == 2


def test_late_flag_compares_dates_not_timestamps(orders, payments, reviews):
    """Delivery at 23:00 on the promised day is on time, not 0.96 days late."""
    fact = transform.build_fact_orders(orders, payments, reviews).set_index("order_id")
    assert fact.loc["on_time", "is_late"] == 0
    assert fact.loc["late", "is_late"] == 1
    assert fact.loc["late", "days_vs_estimate"] == 5


def test_undelivered_orders_have_no_delivery_metrics(orders, payments, reviews):
    fact = transform.build_fact_orders(orders, payments, reviews).set_index("order_id")
    assert fact.loc["not_delivered", "is_delivered"] == 0
    assert pd.isna(fact.loc["not_delivered", "delivery_days"])
    # An undelivered order must never be counted as late.
    assert fact.loc["not_delivered", "is_late"] == 0


def test_cancelled_orders_are_flagged_invalid(orders, payments, reviews):
    fact = transform.build_fact_orders(orders, payments, reviews).set_index("order_id")
    assert fact.loc["cancelled", "is_valid_order"] == 0
    assert fact.loc["on_time", "is_valid_order"] == 1


def test_fact_sales_keeps_item_grain(orders, payments, reviews):
    """Two items on one order must stay two rows, each carrying the order's flags."""
    items = pd.DataFrame({
        "order_id": ["on_time", "on_time", "late"],
        "order_item_id": [1, 2, 1],
        "product_id": ["p1", "p2", "p1"],
        "seller_id": ["s1", "s1", "s2"],
        "shipping_limit_date": pd.to_datetime(["2018-01-05"] * 3),
        "price": [100.0, 50.0, 30.0],
        "freight_value": [10.0, 5.0, 3.0],
    })
    fact_orders = transform.build_fact_orders(orders, payments, reviews)
    sales = transform.build_fact_sales(items, fact_orders)

    assert len(sales) == 3, "item grain must be preserved"
    assert sales["line_total"].sum() == pytest.approx(198.0)
    on_time_rows = sales[sales["order_id"] == "on_time"]
    assert (on_time_rows["review_score"] == 5).all(), "order review copied to each item"


def test_dim_product_falls_back_when_translation_missing():
    products = pd.DataFrame({
        "product_id": ["p1", "p2", "p3"],
        "product_category_name": ["beleza_saude", "pc_gamer", None],
        "product_name_lenght": [40, 30, 20],
        "product_description_lenght": [300, 200, 100],
        "product_photos_qty": [1, 2, 1],
        "product_weight_g": [500, 800, 200],
        "product_length_cm": [10, 20, 5],
        "product_height_cm": [10, 20, 5],
        "product_width_cm": [10, 20, 5],
    })
    translation = pd.DataFrame({
        "product_category_name": ["beleza_saude"],
        "product_category_name_english": ["health_beauty"],
    })
    dim = transform.build_dim_product(products, translation).set_index("product_id")

    assert dim.loc["p1", "category"] == "Health Beauty", "translated and tidied"
    assert dim.loc["p2", "category"] == "Pc Gamer", "falls back to Portuguese name"
    assert dim.loc["p3", "category"] == "Unknown", "never drops a product"
    assert "product_name_length" in dim.columns, "misspelled source column renamed"


def test_dim_date_is_continuous():
    dim = transform.build_dim_date(pd.Timestamp("2017-06-15"), pd.Timestamp("2018-03-02"))
    assert dim["date"].min() == pd.Timestamp("2017-01-01"), "starts at a year boundary"
    assert dim["date"].max() == pd.Timestamp("2018-12-31"), "ends at a year boundary"
    gaps = dim["date"].diff().dropna().dt.days.unique()
    assert list(gaps) == [1], "no gaps allowed, or time intelligence breaks"
