"""
kpis.py — calculate every headline number independently of Power BI.

WHY THIS FILE EXISTS (this is the reconciliation bullet on your resume)
----------------------------------------------------------------------
Anyone can put a number on a dashboard. The question an auditor, a finance manager or a
government reporting team will ask is: "how do you know it's right?"

This module recalculates each KPI from the modelled tables using pandas. The Power BI
report calculates the same KPIs using DAX. Two independent implementations agreeing is
real evidence; one implementation agreeing with itself is not.

If the two disagree, one has a bug — and finding out which is exactly the kind of story
interviewers want to hear.
"""
from __future__ import annotations

import logging

import pandas as pd

from . import config, io_utils

log = logging.getLogger(__name__)


def compute_kpis(model: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Return every headline KPI as a plain dict."""
    sales, orders, customers = model["fact_sales"], model["fact_orders"], model["dim_customer"]

    valid = sales[sales["is_valid_sale"] == 1]
    delivered = orders[orders["is_delivered"] == 1]

    revenue = valid["price"].sum()
    n_orders = valid["order_id"].nunique()
    n_items = len(valid)

    # Real customers = distinct customer_unique_id, NOT customer_id.
    unique_customers = (valid[["customer_id"]]
                        .merge(customers[["customer_id", "customer_unique_id"]], on="customer_id")
                        ["customer_unique_id"].nunique())

    reviewed = orders[orders["review_score"].notna()]
    late_reviews = orders.loc[orders["is_late"] == 1, "review_score"]
    ontime_reviews = orders.loc[(orders["is_delivered"] == 1) & (orders["is_late"] == 0),
                                "review_score"]

    kpis = {
        "Revenue": revenue,
        "Freight": valid["freight_value"].sum(),
        "Gross Order Value": revenue + valid["freight_value"].sum(),
        "Orders": n_orders,
        "Items Sold": n_items,
        "AOV": revenue / n_orders if n_orders else float("nan"),
        "Items per Order": n_items / n_orders if n_orders else float("nan"),
        "Customers": unique_customers,
        "Active Sellers": valid["seller_id"].nunique(),
        "Delivered Orders": len(delivered),
        "Late Orders": int(orders["is_late"].sum()),
        "Late Delivery %": delivered["is_late"].mean() if len(delivered) else float("nan"),
        "Avg Delivery Days": delivered["delivery_days"].mean(),
        "Avg Days vs Estimate": delivered["days_vs_estimate"].mean(),
        "Reviewed Orders": len(reviewed),
        "Avg Review Score": orders["review_score"].mean(),
        "% 5-Star": (reviewed["review_score"] == 5).mean() if len(reviewed) else float("nan"),
        "% Detractors": (reviewed["review_score"] <= 2).mean() if len(reviewed) else float("nan"),
        "Avg Review (Late)": late_reviews.mean(),
        "Avg Review (On Time)": ontime_reviews.mean(),
    }
    kpis["Review Gap (On Time - Late)"] = (kpis["Avg Review (On Time)"]
                                           - kpis["Avg Review (Late)"])
    return kpis


def revenue_by_year(model: dict[str, pd.DataFrame]) -> pd.Series:
    """Yearly revenue, used to sanity-check the year-on-year measures in Power BI."""
    valid = model["fact_sales"][model["fact_sales"]["is_valid_sale"] == 1].copy()
    valid["year"] = pd.to_datetime(valid["order_date"]).dt.year
    return valid.groupby("year")["price"].sum()


def monthly_revenue(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Monthly revenue and orders — used for the trend chart and to decide which
    incomplete months to exclude from the dashboard."""
    valid = model["fact_sales"][model["fact_sales"]["is_valid_sale"] == 1].copy()
    valid["year_month"] = pd.to_datetime(valid["order_date"]).dt.to_period("M").astype(str)
    out = valid.groupby("year_month").agg(
        revenue=("price", "sum"),
        orders=("order_id", "nunique"),
        items=("price", "size"),
    ).reset_index()
    return out


def _fmt(name: str, value: float) -> str:
    """Format a KPI the same way the dashboard does, so comparison is eyeball-easy."""
    if pd.isna(value):
        return "n/a"
    if "%" in name:
        return f"{value:.1%}"
    if name in {"Orders", "Items Sold", "Customers", "Active Sellers",
                "Delivered Orders", "Late Orders", "Reviewed Orders"}:
        return f"{int(value):,}"
    if name in {"Avg Review Score", "Avg Review (Late)", "Avg Review (On Time)",
                "Review Gap (On Time - Late)", "Items per Order"}:
        return f"{value:.2f}"
    if name in {"Avg Delivery Days", "Avg Days vs Estimate"}:
        return f"{value:.1f}"
    return f"{value:,.2f}"


def write_reconciliation(model: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Write docs/reconciliation.md with a blank column for the Power BI value."""
    kpis = compute_kpis(model)

    lines = [
        "# KPI reconciliation",
        "",
        "Values calculated in Python straight from the modelled tables. Open the Power BI "
        "report with **all slicers cleared**, put each measure on a card, and fill in the "
        "second column. Anything that doesn't match is a bug in one of the two engines.",
        "",
        "| KPI | Python (expected) | Power BI (actual) | Match? |",
        "|---|---|---|---|",
    ]
    for name, value in kpis.items():
        lines.append(f"| {name} | {_fmt(name, value)} | | |")

    lines += ["", "## Revenue by year (check the YoY measures)", "",
              "| Year | Revenue |", "|---|---|"]
    for year, value in revenue_by_year(model).items():
        lines.append(f"| {int(year)} | {value:,.2f} |")

    monthly = monthly_revenue(model)
    lines += ["", "## Monthly revenue", "",
              "Use this to choose the date range for trend charts: drop the months at each "
              "end where order volume collapses, and write the decision in the KPI dictionary.",
              "", "| Month | Revenue | Orders |", "|---|---|---|"]
    for _, r in monthly.iterrows():
        lines.append(f"| {r['year_month']} | {r['revenue']:,.2f} | {int(r['orders']):,} |")

    io_utils.write_markdown(lines, "reconciliation.md")

    log.info("Revenue %s | Orders %s | Late %% %s | Review gap %s",
             _fmt("Revenue", kpis["Revenue"]), _fmt("Orders", kpis["Orders"]),
             _fmt("Late Delivery %", kpis["Late Delivery %"]),
             _fmt("Review Gap (On Time - Late)", kpis["Review Gap (On Time - Late)"]))
    return kpis
