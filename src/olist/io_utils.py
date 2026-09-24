"""
io_utils.py — loading raw files, saving outputs, and logging.

WHY THIS FILE EXISTS
--------------------
Reading a CSV looks trivial until it silently corrupts your data. Two real traps in this
dataset:

1. Zip code prefixes like "01037" become the number 1037 if pandas guesses the type,
   and the leading zero is gone forever.
2. The category translation file is saved with a byte-order mark, so the first column
   arrives named "\ufeffproduct_category_name" and every join against it fails.

Centralising the loading rules means those decisions are made once and documented.
"""
from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from . import config

log = logging.getLogger(__name__)

# Columns that must stay text. Losing a leading zero is a silent data-quality bug.
TEXT_COLUMNS = {
    "customer_zip_code_prefix",
    "seller_zip_code_prefix",
    "geolocation_zip_code_prefix",
}

# Columns that must be parsed as timestamps, per file.
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}


def setup_logging(verbose: bool = False) -> None:
    """Log to the console and to logs/pipeline.log.

    A log file is what turns "it broke" into "it broke at 14:02 in the transform stage
    on the reviews join". Interviewers notice when a candidate logs deliberately.
    """
    config.ensure_dirs()
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s | %(levelname)-7s | %(name)-18s | %(message)s"

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()  # avoid duplicate lines when the CLI runs twice in one session

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))
    root.addHandler(console)

    file_handler = logging.FileHandler(config.LOG_DIR / "pipeline.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(file_handler)


@contextmanager
def stage(name: str):
    """Time a pipeline stage and log how long it took.

    Usage:
        with stage("validate"):
            ...
    """
    log.info("START  %s", name)
    started = time.perf_counter()
    try:
        yield
    finally:
        log.info("DONE   %s in %.1fs", name, time.perf_counter() - started)


def load_raw(name: str, data_dir: Path | None = None) -> pd.DataFrame:
    """Load one raw Olist file by its logical name (e.g. "orders").

    Applies the two safety rules: text columns stay text, date columns become datetimes,
    and utf-8-sig strips any byte-order mark.
    """
    data_dir = data_dir or config.DATA_DIR
    path = data_dir / config.FILES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Download the Olist dataset from Kaggle and unzip it into {data_dir}/"
        )

    # Peek at the header first so we only force types on columns that exist.
    header = pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns
    dtypes = {c: "string" for c in header if c in TEXT_COLUMNS}
    dates = [c for c in DATE_COLUMNS.get(name, []) if c in header]

    df = pd.read_csv(path, encoding="utf-8-sig", dtype=dtypes, parse_dates=dates)
    log.info("loaded %-12s %8d rows x %2d cols", name, len(df), df.shape[1])
    return df


def load_all(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load every raw file into a dict keyed by logical name."""
    return {name: load_raw(name, data_dir) for name in config.FILES}


def save_table(df: pd.DataFrame, name: str, folder: Path | None = None) -> Path:
    """Write a model table to CSV for Power BI to read.

    CSV (not Parquet) on purpose: Power BI Desktop reads CSV natively with no extra
    connector, and a reviewer on GitHub can open the file and see what it contains.
    """
    folder = folder or config.MODEL_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info("wrote  %-28s %8d rows -> %s", name, len(df), path.relative_to(config.REPO_ROOT))
    return path


def write_markdown(lines: list[str], filename: str, folder: Path | None = None) -> Path:
    """Write a generated markdown report into docs/."""
    folder = folder or config.DOCS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("wrote  %s", path.relative_to(config.REPO_ROOT))
    return path
