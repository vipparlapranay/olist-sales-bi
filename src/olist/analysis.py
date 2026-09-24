"""
analysis.py — the three analyses that lift this above a standard dashboard project.

WHY THIS FILE EXISTS
--------------------
A dashboard shows *what* happened. These three analyses explain *so what*, and each one
becomes a column or a page in Power BI plus a line on your resume:

1. ABC / Pareto classification  -> every category labelled A, B or C by revenue
   contribution. Feeds a slicer in the report: "show me only A categories".

2. RFM customer segmentation    -> every customer scored on Recency, Frequency and
   Monetary value, then labelled (Champions, At Risk, Hibernating...). Optionally
   cross-checked with K-Means clustering, so you can talk about both a rules-based and
   an unsupervised approach and why you'd choose one.

3. Delivery vs satisfaction significance test -> instead of saying "late orders look
   worse", you prove it: group means, a Mann-Whitney U test (review scores are ordinal,
   not normal, so a t-test alone would be sloppy), and Cliff's delta for effect size.

Being able to say "I tested whether the difference was statistically significant, and
reported effect size, not just the p-value" separates you from most junior candidates.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

from . import config, io_utils

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. ABC / Pareto classification of product categories
# ---------------------------------------------------------------------------

def category_abc(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Rank categories by revenue and label them A, B or C.

    The Pareto principle says a small share of categories drives most revenue. Rather
    than eyeballing a chart, we compute the cumulative share and cut it at 80% and 95%:

        A = the categories that make up the first 80% of revenue  (protect these)
        B = the next 15%                                          (grow these)
        C = the long tail                                         (review or drop)

    Merchandising teams genuinely run stock decisions this way.
    """
    sales, products = model["fact_sales"], model["dim_product"]
    valid = sales[sales["is_valid_sale"] == 1]

    joined = valid.merge(products[["product_id", "category"]], on="product_id", how="left")
    joined["category"] = joined["category"].fillna("Unknown")

    agg = joined.groupby("category").agg(
        revenue=("price", "sum"),
        items_sold=("price", "size"),
        orders=("order_id", "nunique"),
        avg_review=("review_score", "mean"),
    ).reset_index()

    agg = agg.sort_values("revenue", ascending=False).reset_index(drop=True)
    agg["revenue_rank"] = np.arange(1, len(agg) + 1)
    agg["revenue_share"] = agg["revenue"] / agg["revenue"].sum()
    agg["cumulative_share"] = agg["revenue_share"].cumsum()

    agg["abc_class"] = np.where(
        agg["cumulative_share"] <= config.ABC_A_CUTOFF, "A",
        np.where(agg["cumulative_share"] <= config.ABC_B_CUTOFF, "B", "C"),
    )
    # The first category always belongs to A even if it alone exceeds the cutoff.
    agg.loc[0, "abc_class"] = "A"

    n_a = int((agg["abc_class"] == "A").sum())
    log.info("ABC: %d of %d categories (%.0f%%) generate 80%% of revenue",
             n_a, len(agg), 100 * n_a / len(agg))
    return agg


# ---------------------------------------------------------------------------
# 2. RFM customer segmentation
# ---------------------------------------------------------------------------

def rfm_segments(model: dict[str, pd.DataFrame], n_clusters: int = 4) -> pd.DataFrame:
    """Score every customer on Recency, Frequency and Monetary value, then segment.

    Definitions (the standard ones):
        Recency   = days between the customer's last order and the end of the dataset
        Frequency = number of orders placed
        Monetary  = total revenue from that customer

    Each dimension is split into quintiles scored 1-5. Recency is reversed, because a
    SMALL number of days is GOOD. The three scores combine into business labels.

    A K-Means cluster label is added alongside as a cross-check. Two methods landing on
    similar groups is reassuring; where they disagree is worth a sentence in your README.
    """
    sales, customers = model["fact_sales"], model["dim_customer"]
    valid = sales[sales["is_valid_sale"] == 1].copy()

    # Map each order to the real person behind it.
    valid = valid.merge(customers[["customer_id", "customer_unique_id"]],
                        on="customer_id", how="left")
    valid["order_date"] = pd.to_datetime(valid["order_date"])

    # "Today" for a historical dataset = the day after the last order, so recency is
    # never zero and the result is reproducible (never depends on when you run it).
    snapshot = valid["order_date"].max() + pd.Timedelta(days=1)

    rfm = valid.groupby("customer_unique_id").agg(
        last_order=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum"),
    ).reset_index()
    rfm["recency_days"] = (snapshot - rfm["last_order"]).dt.days

    def score(series: pd.Series, reverse: bool = False) -> pd.Series:
        """Quintile score 1-5. Falls back gracefully when values are heavily tied."""
        try:
            ranks = pd.qcut(series.rank(method="first"), config.RFM_QUANTILES, labels=False) + 1
        except ValueError:  # not enough distinct values to cut
            ranks = pd.Series(np.full(len(series), 3), index=series.index)
        return (config.RFM_QUANTILES + 1 - ranks) if reverse else ranks

    rfm["r_score"] = score(rfm["recency_days"], reverse=True)  # recent = high score
    rfm["f_score"] = score(rfm["frequency"])
    rfm["m_score"] = score(rfm["monetary"])
    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    def label(row) -> str:
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4:
            return "Champions"
        if r >= 3 and m >= 4:
            return "Big Spenders"
        if r >= 4:
            return "Recent Customers"
        if r <= 2 and m >= 4:
            return "At Risk (high value)"
        if r <= 2:
            return "Hibernating"
        return "Needs Attention"

    rfm["segment"] = rfm.apply(label, axis=1)

    # --- K-Means cross-check on log-scaled, standardised features.
    # Log scaling because monetary value is heavily skewed; standardising because
    # K-Means uses Euclidean distance and would otherwise be dominated by the
    # largest-range feature.
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        from sklearn.preprocessing import StandardScaler

        features = np.column_stack([
            np.log1p(rfm["recency_days"]),
            np.log1p(rfm["frequency"]),
            np.log1p(rfm["monetary"]),
        ])
        scaled = StandardScaler().fit_transform(features)
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=config.ML_RANDOM_STATE)
        rfm["kmeans_cluster"] = km.fit_predict(scaled)

        # Silhouette on a sample keeps it fast on ~100k customers.
        sample = min(5000, len(scaled))
        idx = np.random.default_rng(config.ML_RANDOM_STATE).choice(len(scaled), sample, replace=False)
        sil = silhouette_score(scaled[idx], rfm["kmeans_cluster"].values[idx])
        log.info("K-Means: %d clusters, silhouette %.3f", n_clusters, sil)
        rfm.attrs["silhouette"] = round(float(sil), 3)
    except Exception as exc:  # scikit-learn missing or degenerate data
        log.warning("K-Means step skipped: %s", exc)
        rfm["kmeans_cluster"] = -1

    log.info("RFM: %d customers segmented; largest segment = %s",
             len(rfm), rfm["segment"].value_counts().idxmax())
    return rfm.drop(columns=["last_order"])


# ---------------------------------------------------------------------------
# 3. Does late delivery actually hurt satisfaction?
# ---------------------------------------------------------------------------

def _cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """Effect size for ordinal data, derived from the Mann-Whitney U statistic.

    Ranges from -1 to +1. Rough reading: <0.15 negligible, <0.33 small,
    <0.47 medium, above that large. A tiny p-value on 90,000 rows means almost
    nothing on its own; effect size is what tells you whether anyone should care.
    """
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
    return float(2 * u / (len(a) * len(b)) - 1)


def delivery_satisfaction_test(model: dict[str, pd.DataFrame]) -> dict:
    """Compare review scores for late vs on-time deliveries, with a significance test."""
    orders = model["fact_orders"]
    delivered = orders[(orders["is_delivered"] == 1) & orders["review_score"].notna()]

    late = delivered.loc[delivered["is_late"] == 1, "review_score"].to_numpy()
    ontime = delivered.loc[delivered["is_late"] == 0, "review_score"].to_numpy()

    if len(late) < 30 or len(ontime) < 30:
        log.warning("Not enough data for the significance test")
        return {}

    # Mann-Whitney U: review scores are ordinal (1-5) and far from normal, so a rank
    # test is the honest choice. Welch's t-test is reported alongside for readers who
    # expect it; both agreeing strengthens the conclusion.
    u_stat, p_value = stats.mannwhitneyu(ontime, late, alternative="greater")
    t_stat, t_p = stats.ttest_ind(ontime, late, equal_var=False)
    delta = _cliffs_delta(ontime, late)

    # 95% confidence interval for the difference in means (Welch).
    diff = ontime.mean() - late.mean()
    se = np.sqrt(ontime.var(ddof=1) / len(ontime) + late.var(ddof=1) / len(late))
    ci = (diff - 1.96 * se, diff + 1.96 * se)

    result = {
        "n_ontime": len(ontime), "n_late": len(late),
        "mean_ontime": float(ontime.mean()), "mean_late": float(late.mean()),
        "difference": float(diff), "ci_low": float(ci[0]), "ci_high": float(ci[1]),
        "mannwhitney_u": float(u_stat), "p_value": float(p_value),
        "welch_t": float(t_stat), "welch_p": float(t_p),
        "cliffs_delta": delta,
        "pct_1star_late": float((late == 1).mean()),
        "pct_1star_ontime": float((ontime == 1).mean()),
    }
    log.info("Review score: on-time %.2f vs late %.2f (difference %.2f, p=%.2e, delta=%.2f)",
             result["mean_ontime"], result["mean_late"], diff, p_value, delta)
    return result


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_analysis_report(abc: pd.DataFrame, rfm: pd.DataFrame, test: dict) -> None:
    """Write docs/analysis_report.md — the evidence behind your dashboard insights."""
    total_rev = abc["revenue"].sum()
    a_count = int((abc["abc_class"] == "A").sum())
    a_share = abc.loc[abc["abc_class"] == "A", "revenue"].sum() / total_rev

    lines = [
        "# Analysis report", "",
        "Generated by `python -m olist.pipeline analyse`. Every figure here is reproducible.",
        "",
        "## 1. Category concentration (ABC / Pareto)", "",
        f"- {len(abc)} categories generated {total_rev:,.0f} in revenue.",
        f"- **{a_count} categories ({a_count / len(abc):.0%}) generate "
        f"{a_share:.0%} of revenue** — these are class A.",
        f"- Class B: {int((abc['abc_class'] == 'B').sum())} categories. "
        f"Class C (long tail): {int((abc['abc_class'] == 'C').sum())}.",
        "",
        "### Top 10 categories", "",
        "| Rank | Category | Revenue | Share | Cumulative | Class | Avg review |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in abc.head(10).iterrows():
        lines.append(
            f"| {int(r['revenue_rank'])} | {r['category']} | {r['revenue']:,.0f} "
            f"| {r['revenue_share']:.1%} | {r['cumulative_share']:.1%} | {r['abc_class']} "
            f"| {r['avg_review']:.2f} |"
        )

    lines += ["", "### Bottom 5 categories by revenue", "",
              "| Category | Revenue | Items sold | Avg review |", "|---|---|---|---|"]
    for _, r in abc.tail(5).iterrows():
        lines.append(f"| {r['category']} | {r['revenue']:,.0f} | {int(r['items_sold'])} "
                     f"| {r['avg_review']:.2f} |")

    seg_counts = rfm["segment"].value_counts()
    seg_value = rfm.groupby("segment")["monetary"].sum().sort_values(ascending=False)
    lines += ["", "## 2. Customer segmentation (RFM)", "",
              f"- {len(rfm):,} unique customers scored on recency, frequency and monetary value.",
              f"- Repeat customers: {(rfm['frequency'] > 1).sum():,} "
              f"({(rfm['frequency'] > 1).mean():.1%} of the base).",
              "", "| Segment | Customers | Share | Total value | Avg value |",
              "|---|---|---|---|---|"]
    for seg in seg_counts.index:
        sub = rfm[rfm["segment"] == seg]
        lines.append(f"| {seg} | {len(sub):,} | {len(sub) / len(rfm):.1%} "
                     f"| {seg_value[seg]:,.0f} | {sub['monetary'].mean():,.0f} |")
    if "silhouette" in rfm.attrs:
        lines += ["", f"K-Means cross-check: silhouette score {rfm.attrs['silhouette']} "
                      "(higher is better; below ~0.25 means the clusters overlap heavily, "
                      "which is common for RFM data and is why the rules-based segments "
                      "are used for reporting)."]

    if test:
        lines += ["", "## 3. Does late delivery hurt satisfaction?", "",
                  f"- On-time deliveries: **{test['mean_ontime']:.2f}** average review "
                  f"(n = {test['n_ontime']:,})",
                  f"- Late deliveries: **{test['mean_late']:.2f}** average review "
                  f"(n = {test['n_late']:,})",
                  f"- Difference: **{test['difference']:.2f} stars** "
                  f"(95% CI {test['ci_low']:.2f} to {test['ci_high']:.2f})",
                  f"- Mann-Whitney U test: p = {test['p_value']:.3e}",
                  f"- Cliff's delta (effect size): {test['cliffs_delta']:.2f}",
                  f"- 1-star reviews: {test['pct_1star_late']:.1%} of late orders vs "
                  f"{test['pct_1star_ontime']:.1%} of on-time orders",
                  "",
                  "**Reading it:** the p-value only says the difference is unlikely to be "
                  "chance, which is easy to achieve with tens of thousands of rows. The "
                  "effect size and the gap in 1-star reviews are what make this worth "
                  "acting on.",
                  "",
                  "**Caveat to state out loud:** this is observational data, so it shows "
                  "association, not proof of cause. Orders that run late may differ in "
                  "other ways too (distance, product type, seller).",
                  ]

    io_utils.write_markdown(lines, "analysis_report.md")
