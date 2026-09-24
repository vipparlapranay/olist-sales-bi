"""
config.py — every path and business rule lives here, nowhere else.

WHY THIS FILE EXISTS
--------------------
The fastest way to make a pipeline unmaintainable is to scatter magic values through
the code: a folder path in one script, a "canceled" string in another, a date cut-off in
a third. When the business changes a rule you then have to hunt for it.

Everything tunable sits in this one module, so a reviewer can read this file and know
exactly how the numbers are defined. This is also the answer to the interview question
"how would you make this production-ready?".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths. Everything is relative to the repo root, so the project runs the same
# on your laptop, on a colleague's machine, and in GitHub Actions.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = REPO_ROOT / "data"                 # raw Kaggle CSVs (git-ignored)
OUTPUT_DIR = REPO_ROOT / "outputs"            # everything the pipeline produces
MODEL_DIR = OUTPUT_DIR / "model"              # star-schema tables Power BI reads
FIGURE_DIR = OUTPUT_DIR / "figures"           # charts for the README
DOCS_DIR = REPO_ROOT / "docs"                 # generated markdown reports
LOG_DIR = REPO_ROOT / "logs"

# Raw file names, kept in one place so a rename upstream is a one-line change.
FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "translation": "product_category_name_translation.csv",
}

# ---------------------------------------------------------------------------
# Business rules. These must match the Power Query / DAX definitions exactly,
# otherwise the two engines will disagree and reconciliation will fail.
# ---------------------------------------------------------------------------

# Orders in these statuses never became a sale, so they are excluded from revenue.
INVALID_ORDER_STATUSES = frozenset({"canceled", "unavailable"})

# An order counts as delivered only if the status says so AND a delivery date exists.
DELIVERED_STATUS = "delivered"

# "Late" = the customer received the order after the promised date, compared at
# whole-day level (a delivery at 23:00 on the promised day is NOT late).
LATE_THRESHOLD_DAYS = 0

# ABC classification thresholds on cumulative revenue share (Pareto principle).
ABC_A_CUTOFF = 0.80   # categories making up the first 80% of revenue
ABC_B_CUTOFF = 0.95   # the next 15%

# RFM segmentation: how many buckets to split each dimension into.
RFM_QUANTILES = 5

# Machine learning: how much of the timeline to hold out for testing.
# A TIME-BASED split, not a random one — you cannot use next month's orders to
# predict last month's. Random splits leak the future and inflate scores.
ML_TEST_FRACTION = 0.20
ML_RANDOM_STATE = 42
ML_MIN_CATEGORY_FREQ = 200  # rarer categories get grouped into "other"


@dataclass(frozen=True)
class BrazilRegions:
    """State code -> (state name, region). Used for maps and row-level security."""

    mapping: dict[str, tuple[str, str]] = field(default_factory=lambda: {
        "AC": ("Acre", "North"), "AP": ("Amapa", "North"), "AM": ("Amazonas", "North"),
        "PA": ("Para", "North"), "RO": ("Rondonia", "North"), "RR": ("Roraima", "North"),
        "TO": ("Tocantins", "North"),
        "AL": ("Alagoas", "Northeast"), "BA": ("Bahia", "Northeast"),
        "CE": ("Ceara", "Northeast"), "MA": ("Maranhao", "Northeast"),
        "PB": ("Paraiba", "Northeast"), "PE": ("Pernambuco", "Northeast"),
        "PI": ("Piaui", "Northeast"), "RN": ("Rio Grande do Norte", "Northeast"),
        "SE": ("Sergipe", "Northeast"),
        "DF": ("Distrito Federal", "Center-West"), "GO": ("Goias", "Center-West"),
        "MT": ("Mato Grosso", "Center-West"), "MS": ("Mato Grosso do Sul", "Center-West"),
        "ES": ("Espirito Santo", "Southeast"), "MG": ("Minas Gerais", "Southeast"),
        "RJ": ("Rio de Janeiro", "Southeast"), "SP": ("Sao Paulo", "Southeast"),
        "PR": ("Parana", "South"), "RS": ("Rio Grande do Sul", "South"),
        "SC": ("Santa Catarina", "South"),
    })

    def to_frame(self):
        """Return the mapping as a DataFrame so it can be joined like any other table."""
        import pandas as pd

        return pd.DataFrame(
            [(code, name, region) for code, (name, region) in self.mapping.items()],
            columns=["state_code", "state_name", "region"],
        )


def ensure_dirs() -> None:
    """Create every output folder up front so later stages never fail on a missing path."""
    for folder in (OUTPUT_DIR, MODEL_DIR, FIGURE_DIR, DOCS_DIR, LOG_DIR):
        folder.mkdir(parents=True, exist_ok=True)
