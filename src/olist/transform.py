"""
transform.py — turn 9 raw tables into a star schema.

WHY THIS FILE EXISTS
--------------------
Power BI can technically load the raw CSVs, but then every report question becomes a
wrestling match with grain. This module does the modelling once, in code that can be
version-controlled, reviewed and unit-tested, and writes tidy tables Power BI just reads.

THE GRAIN PROBLEM (the core idea of the whole project)
------------------------------------------------------
- Revenue is measured per ITEM: an order with 3 items has 3 prices.
- Delivery time and review score are measured per ORDER: that order has ONE delivery.

Put both in one table and "average delivery days" counts that order three times. So we
build two fact tables at their natural grain, sharing the same dimensions:

    Fact_Sales   -> one row per order item  (revenue, product, seller)
    Fact_Orders  -> one row per order       (delivery, payment, review)

Both connect to Dim_Date, Dim_Customer; Fact_Sales also connects to Dim_Product and
Dim_Seller. Facts never join to each other directly.

The rules here mirror the Power Query scripts in powerquery/ exactly, which is what
makes the two engines reconcile.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

def build_dim_date(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """A continuous calendar covering whole years around the data.

    Time-intelligence calculations need every date present with no gaps, including
    dates with no sales. Building it from the data's min/max would leave holes.
    """
    first = pd.Timestamp(year=start.year, month=1, day=1)
    last = pd.Timestamp(year=end.year, month=12, day=31)
    dates = pd.date_range(first, last, freq="D")

    dim = pd.DataFrame({"date": dates})
    dim["year"] = dim["date"].dt.year
    dim["quarter"] = "Q" + dim["date"].dt.quarter.astype(str)
    dim["month_no"] = dim["date"].dt.month
    dim["month"] = dim["date"].dt.strftime("%b")
    dim["year_month"] = dim["date"].dt.strftime("%Y-%m")
    dim["year_month_sort"] = dim["year"] * 100 + dim["month_no"]
    dim["weekday_no"] = dim["date"].dt.dayofweek + 1          # Monday = 1
    dim["weekday"] = dim["date"].dt.strftime("%a")
    dim["is_weekend"] = np.where(dim["weekday_no"] > 5, "Weekend", "Weekday")
    return dim


def _add_region(df: pd.DataFrame, state_col: str, prefix: str) -> pd.DataFrame:
    """Join the state-code lookup on and give the new columns a readable prefix."""
    states = config.BrazilRegions().to_frame()
    out = df.merge(states, left_on=state_col, right_on="state_code", how="left")
    return out.drop(columns=["state_code"]).rename(columns={
        "state_name": f"{prefix}_state_name",
        "region": f"{prefix}_region",
    })


def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    """One row per customer_id.

    IMPORTANT: in this dataset customer_id is generated per ORDER. The real person is
    customer_unique_id. Any "number of customers" measure must count the unique id,
    otherwise every repeat buyer is counted again. This trap is worth memorising.
    """
    dim = customers.copy()
    dim["customer_city"] = dim["customer_city"].str.title()
    dim = _add_region(dim, "customer_state", "customer")
    return dim.rename(columns={
        "customer_city": "customer_city_name",
        "customer_state": "customer_state_code",
    })


def build_dim_product(products: pd.DataFrame, translation: pd.DataFrame) -> pd.DataFrame:
    """One row per product, with a clean English category.

    Fallback chain: English name -> Portuguese name -> "Unknown". A few categories are
    missing from the translation file and some products have no category at all, so
    without the fallback those rows would vanish from category charts.
    """
    dim = products.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    }).copy()

    dim = dim.merge(translation, on="product_category_name", how="left")

    category = (dim["product_category_name_english"]
                .fillna(dim["product_category_name"])
                .fillna("unknown")
                .str.replace("_", " ", regex=False)
                .str.title())
    dim["category"] = category
    return dim.drop(columns=["product_category_name_english"])


def build_dim_seller(sellers: pd.DataFrame) -> pd.DataFrame:
    """One row per seller, with state name and region for mapping."""
    dim = sellers.copy()
    dim["seller_city"] = dim["seller_city"].str.title()
    dim = _add_region(dim, "seller_state", "seller")
    return dim.rename(columns={
        "seller_city": "seller_city_name",
        "seller_state": "seller_state_code",
    })


# ---------------------------------------------------------------------------
# Grain-fixing aggregations
# ---------------------------------------------------------------------------

def aggregate_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """Collapse payment lines to one row per order.

    An order paid with a voucher plus a credit card has two rows here. Joining that
    straight onto orders would duplicate the order; joining onto items would multiply
    revenue. So we aggregate FIRST, then join.
    """
    grouped = payments.groupby("order_id")
    out = grouped.agg(
        payment_value=("payment_value", "sum"),
        max_installments=("payment_installments", "max"),
        payment_lines=("payment_value", "size"),
    ).reset_index()

    # The "main" payment type = the method that paid the largest share.
    main = (payments.sort_values("payment_value")
                    .groupby("order_id", as_index=False)
                    .tail(1)[["order_id", "payment_type"]]
                    .rename(columns={"payment_type": "main_payment_type"}))
    return out.merge(main, on="order_id", how="left")


def aggregate_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """Collapse reviews to one row per order, keeping the LATEST review.

    Some orders were reviewed more than once (the customer updated their opinion).
    Averaging the scores would blend a 1 and a 5 into a meaningless 3, so we take the
    most recently answered review and record how many existed.
    """
    latest = (reviews.sort_values("review_answer_timestamp")
                     .groupby("order_id", as_index=False)
                     .tail(1)[["order_id", "review_score"]])
    counts = reviews.groupby("order_id").size().rename("review_count").reset_index()
    return latest.merge(counts, on="order_id", how="left")


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------

def build_fact_orders(orders: pd.DataFrame, payments: pd.DataFrame,
                      reviews: pd.DataFrame) -> pd.DataFrame:
    """One row per order: delivery performance, payment behaviour, satisfaction."""
    fact = orders.merge(aggregate_payments(payments), on="order_id", how="left")
    fact = fact.merge(aggregate_reviews(reviews), on="order_id", how="left")

    fact["order_date"] = fact["order_purchase_timestamp"].dt.date

    # Delivered = the status says delivered AND we actually have a delivery date.
    fact["is_delivered"] = (
        (fact["order_status"] == config.DELIVERED_STATUS)
        & fact["order_delivered_customer_date"].notna()
    ).astype(int)

    # Days from purchase to delivery (blank for undelivered orders).
    delivery_days = (fact["order_delivered_customer_date"]
                     - fact["order_purchase_timestamp"]).dt.days
    fact["delivery_days"] = delivery_days.where(fact["is_delivered"] == 1)

    # Promise length: how many days the customer was told to expect. This is a feature
    # for the ML model later, and interesting on its own.
    fact["promised_days"] = (fact["order_estimated_delivery_date"]
                             - fact["order_purchase_timestamp"]).dt.days

    # Late = delivered after the promised DAY. Comparing dates (not timestamps) matters:
    # arriving at 23:00 on the promised day is on time, not 0.96 days late.
    days_vs_estimate = (fact["order_delivered_customer_date"].dt.normalize()
                        - fact["order_estimated_delivery_date"].dt.normalize()).dt.days
    fact["days_vs_estimate"] = days_vs_estimate.where(fact["is_delivered"] == 1)
    fact["is_late"] = ((fact["days_vs_estimate"] > config.LATE_THRESHOLD_DAYS)
                       .fillna(False).astype(int))

    # Cancelled and unavailable orders are not sales.
    fact["is_valid_order"] = (~fact["order_status"]
                              .isin(config.INVALID_ORDER_STATUSES)).astype(int)

    log.info("Fact_Orders: %d orders, %d delivered, %d late",
             len(fact), int(fact["is_delivered"].sum()), int(fact["is_late"].sum()))
    return fact


def build_fact_sales(items: pd.DataFrame, fact_orders: pd.DataFrame) -> pd.DataFrame:
    """One row per order item: revenue, product and seller analysis.

    Order-level flags (is_late, review_score) are copied down deliberately so the
    dashboard can answer "which categories get the worst reviews?". That is controlled
    denormalisation: fine for slicing, wrong for averaging delivery time. Be ready to
    explain the difference in an interview.
    """
    order_cols = ["order_id", "customer_id", "order_status", "order_date",
                  "is_delivered", "is_late", "review_score", "is_valid_order"]
    fact = items.merge(fact_orders[order_cols], on="order_id", how="left")

    fact = fact.rename(columns={"is_valid_order": "is_valid_sale"})
    fact["line_total"] = fact["price"] + fact["freight_value"]
    fact = fact.drop(columns=["shipping_limit_date"], errors="ignore")

    log.info("Fact_Sales: %d items across %d orders",
             len(fact), fact["order_id"].nunique())
    return fact


# ---------------------------------------------------------------------------
# Orchestration for this stage
# ---------------------------------------------------------------------------

def build_star_schema(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build every model table and return them in a dict ready to save."""
    fact_orders = build_fact_orders(frames["orders"], frames["payments"], frames["reviews"])
    fact_sales = build_fact_sales(frames["items"], fact_orders)

    purchase = frames["orders"]["order_purchase_timestamp"]
    model = {
        "dim_date": build_dim_date(purchase.min(), purchase.max()),
        "dim_customer": build_dim_customer(frames["customers"]),
        "dim_product": build_dim_product(frames["products"], frames["translation"]),
        "dim_seller": build_dim_seller(frames["sellers"]),
        "fact_orders": fact_orders,
        "fact_sales": fact_sales,
    }
    return model
