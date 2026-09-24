"""
viz.py — four charts for the README, so the repo shows something before anyone opens Power BI.

These are not a replacement for the dashboard. A recruiter scrolling GitHub on their
phone will never open a .pbix file, but they will look at an image. Each chart is saved
to outputs/figures/ and embedded in the README.

matplotlib only, no seaborn, and no explicit colours beyond a single accent — the charts
should look calm and readable, not decorated.
"""
from __future__ import annotations

import logging

import matplotlib
matplotlib.use("Agg")  # non-interactive backend: required for scripts and CI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config

log = logging.getLogger(__name__)

ACCENT = "#2F6FB2"
MUTED = "#B9C4CC"
BAD = "#B8465A"


def _style(ax) -> None:
    """One consistent look: no top/right spines, light horizontal gridlines only."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)


def _save(fig, name: str) -> None:
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURE_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("wrote  %s", path.relative_to(config.REPO_ROOT))


def plot_revenue_trend(monthly: pd.DataFrame) -> None:
    """Monthly revenue with a 3-month rolling average, the standard trend view."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = range(len(monthly))
    ax.plot(x, monthly["revenue"], color=ACCENT, linewidth=2, label="Monthly revenue")
    ax.plot(x, monthly["revenue"].rolling(3).mean(), color=BAD, linewidth=1.5,
            linestyle="--", label="3-month average")

    step = max(1, len(monthly) // 12)
    ax.set_xticks(list(x)[::step])
    ax.set_xticklabels(monthly["year_month"][::step], rotation=45, ha="right")
    ax.set_ylabel("Revenue (BRL)")
    ax.set_title("Revenue by month", loc="left", fontsize=13, fontweight="bold")
    ax.legend(frameon=False)
    _style(ax)
    _save(fig, "revenue_trend")


def plot_pareto(abc: pd.DataFrame, top_n: int = 20) -> None:
    """Pareto chart: bars for revenue, line for cumulative share, 80% reference line."""
    data = abc.head(top_n)
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = [ACCENT if c == "A" else MUTED for c in data["abc_class"]]
    ax.bar(range(len(data)), data["revenue"], color=colors)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(data["category"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Revenue (BRL)")
    _style(ax)

    ax2 = ax.twinx()
    ax2.plot(range(len(data)), data["cumulative_share"] * 100, color=BAD, marker="o",
             markersize=3, linewidth=1.5)
    ax2.axhline(80, color=BAD, linestyle=":", linewidth=1)
    ax2.set_ylabel("Cumulative share (%)")
    ax2.set_ylim(0, 105)
    for side in ("top",):
        ax2.spines[side].set_visible(False)

    n_a = int((abc["abc_class"] == "A").sum())
    ax.set_title(f"Revenue concentration: {n_a} of {len(abc)} categories make up 80% of revenue",
                 loc="left", fontsize=13, fontweight="bold")
    _save(fig, "category_pareto")


def plot_review_by_delivery(model: dict[str, pd.DataFrame]) -> None:
    """Review score distribution for late vs on-time orders — the headline finding."""
    orders = model["fact_orders"]
    delivered = orders[(orders["is_delivered"] == 1) & orders["review_score"].notna()]
    late = delivered[delivered["is_late"] == 1]["review_score"]
    ontime = delivered[delivered["is_late"] == 0]["review_score"]
    if late.empty or ontime.empty:
        return

    scores = [1, 2, 3, 4, 5]
    late_pct = [(late == s).mean() * 100 for s in scores]
    ontime_pct = [(ontime == s).mean() * 100 for s in scores]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.38
    idx = np.arange(len(scores))
    ax.bar(idx - width / 2, ontime_pct, width, color=ACCENT,
           label=f"On time (avg {ontime.mean():.2f})")
    ax.bar(idx + width / 2, late_pct, width, color=BAD,
           label=f"Late (avg {late.mean():.2f})")
    ax.set_xticks(idx)
    ax.set_xticklabels([f"{s} star" for s in scores])
    ax.set_ylabel("Share of orders (%)")
    ax.set_title("Late deliveries collapse into 1-star reviews", loc="left",
                 fontsize=13, fontweight="bold")
    ax.legend(frameon=False)
    _style(ax)
    _save(fig, "review_by_delivery")


def plot_feature_importance(importance: pd.DataFrame, kind: str = "importance") -> None:
    """Horizontal bar chart of the model's top features."""
    if importance is None or importance.empty:
        return
    data = importance.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(data["feature"], data["importance"], color=ACCENT)
    ax.set_xlabel(kind)
    ax.set_title("What predicts a late delivery", loc="left", fontsize=13, fontweight="bold")
    _style(ax)
    ax.grid(axis="y", visible=False)
    _save(fig, "late_risk_features")
