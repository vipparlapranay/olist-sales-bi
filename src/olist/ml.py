"""
ml.py — predict which orders will be delivered late, and feed the score back into the dashboard.

WHY THIS FILE EXISTS (your strongest differentiator on this project)
-------------------------------------------------------------------
The dashboard tells the business what already went wrong. This model flags orders that
are likely to go wrong, at the moment they are placed. The predicted probability is
written to outputs/model/fact_order_risk.csv, which Power BI joins onto Fact_Orders, so
the report gets an "at-risk orders" page. A BI dashboard with a model behind it is rare
in a junior portfolio.

THREE DECISIONS THAT MATTER (be ready to defend all three)
----------------------------------------------------------
1. TIME-BASED SPLIT, not random. We train on the earliest 80% of orders and test on the
   most recent 20%. A random split lets the model peek at the future, which inflates the
   score and would never survive production.

2. ONLY FEATURES KNOWN AT ORDER TIME. No delivery date, no review, no actual transit
   time. Including those would be target leakage: a perfect model that is useless,
   because you would not have those values when you need the prediction.

3. BASELINE FIRST. Logistic regression before random forest. If the simple model is
   almost as good, ship the simple model: it is faster, explainable, and easier to
   maintain. Reporting both shows judgement, not just tool use.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config, io_utils

log = logging.getLogger(__name__)


def build_features(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Assemble one row per delivered order using only order-time information."""
    orders, sales = model["fact_orders"], model["fact_sales"]
    products, customers, sellers = model["dim_product"], model["dim_customer"], model["dim_seller"]

    # Only delivered orders have a known outcome to learn from.
    base = orders[orders["is_delivered"] == 1].copy()

    # Order-level basket features, aggregated from the item grain.
    basket = sales.groupby("order_id").agg(
        n_items=("order_item_id", "count"),
        order_value=("price", "sum"),
        freight_total=("freight_value", "sum"),
        n_sellers=("seller_id", "nunique"),
        main_product=("product_id", "first"),
        main_seller=("seller_id", "first"),
    ).reset_index()

    df = base.merge(basket, on="order_id", how="inner")

    # Product attributes (size and weight drive shipping difficulty).
    prod_cols = ["product_id", "category", "product_weight_g",
                 "product_length_cm", "product_height_cm", "product_width_cm"]
    df = df.merge(products[prod_cols], left_on="main_product", right_on="product_id", how="left")

    # Geography: crossing the country takes longer than a local delivery.
    df = df.merge(customers[["customer_id", "customer_state_code", "customer_region"]],
                  on="customer_id", how="left")
    df = df.merge(sellers[["seller_id", "seller_state_code", "seller_region"]],
                  left_on="main_seller", right_on="seller_id", how="left")

    # Engineered features — this is where domain thinking shows.
    df["same_state"] = (df["customer_state_code"] == df["seller_state_code"]).astype(int)
    df["same_region"] = (df["customer_region"] == df["seller_region"]).astype(int)
    df["freight_ratio"] = df["freight_total"] / df["order_value"].replace(0, np.nan)
    df["product_volume_cm3"] = (df["product_length_cm"] * df["product_height_cm"]
                                * df["product_width_cm"])
    df["purchase_month"] = df["order_purchase_timestamp"].dt.month
    df["purchase_weekday"] = df["order_purchase_timestamp"].dt.dayofweek
    df["purchase_hour"] = df["order_purchase_timestamp"].dt.hour
    # A short promise is harder to keep — often the single strongest predictor.
    df["promised_days"] = df["promised_days"].fillna(df["promised_days"].median())

    # Rare categories add noise and blow up one-hot width, so group them.
    counts = df["category"].value_counts()
    keep = counts[counts >= config.ML_MIN_CATEGORY_FREQ].index
    df["category_grouped"] = np.where(df["category"].isin(keep), df["category"], "Other")

    return df


FEATURES_NUMERIC = [
    "n_items", "order_value", "freight_total", "n_sellers", "freight_ratio",
    "product_weight_g", "product_volume_cm3", "same_state", "same_region",
    "promised_days", "purchase_month", "purchase_weekday", "purchase_hour",
]
FEATURES_CATEGORICAL = ["category_grouped", "customer_region", "seller_region"]


def train_and_evaluate(model: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict]:
    """Train the models, evaluate on a held-out future period, return risk scores."""
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (average_precision_score, classification_report,
                                 confusion_matrix, roc_auc_score)
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    df = build_features(model).sort_values("order_purchase_timestamp").reset_index(drop=True)
    y = df["is_late"].to_numpy()

    if y.sum() < 50:
        log.warning("Too few late orders (%d) to train a useful model", int(y.sum()))
        return pd.DataFrame(), {}

    # --- Time-based split: train on the past, test on the future.
    cut = int(len(df) * (1 - config.ML_TEST_FRACTION))
    train_idx, test_idx = df.index[:cut], df.index[cut:]
    split_date = df.loc[cut, "order_purchase_timestamp"]
    log.info("Train: %d orders before %s | Test: %d orders after",
             len(train_idx), split_date.date(), len(test_idx))

    X = df[FEATURES_NUMERIC + FEATURES_CATEGORICAL]

    # Preprocessing: impute then scale numerics, one-hot the categoricals.
    # Doing this inside a Pipeline is what stops statistics from the test set leaking
    # into training — a very common junior mistake.
    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # older scikit-learn
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)

    pre = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), FEATURES_NUMERIC),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                          ("onehot", ohe)]), FEATURES_CATEGORICAL),
    ])

    candidates = {
        # class_weight="balanced" because late orders are the minority; without it the
        # model can score well by predicting "never late" and being useless.
        "Logistic Regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=config.ML_RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=20, class_weight="balanced_subsample",
            n_jobs=-1, random_state=config.ML_RANDOM_STATE),
    }

    metrics, fitted = {}, {}
    for name, estimator in candidates.items():
        pipe = Pipeline([("pre", pre), ("clf", estimator)])
        pipe.fit(X.loc[train_idx], y[train_idx])
        proba = pipe.predict_proba(X.loc[test_idx])[:, 1]
        preds = (proba >= 0.5).astype(int)

        metrics[name] = {
            "roc_auc": roc_auc_score(y[test_idx], proba),
            # PR-AUC is the honest metric for imbalanced problems; ROC-AUC flatters them.
            "pr_auc": average_precision_score(y[test_idx], proba),
            "baseline_rate": float(y[test_idx].mean()),
            "report": classification_report(y[test_idx], preds, digits=3, zero_division=0),
            "confusion": confusion_matrix(y[test_idx], preds).tolist(),
        }
        fitted[name] = pipe
        log.info("%-20s ROC-AUC %.3f | PR-AUC %.3f (base rate %.3f)",
                 name, metrics[name]["roc_auc"], metrics[name]["pr_auc"],
                 metrics[name]["baseline_rate"])

    best_name = max(metrics, key=lambda k: metrics[k]["pr_auc"])
    best = fitted[best_name]
    log.info("Best model on PR-AUC: %s", best_name)

    # --- Feature importance, in the model's own terms.
    feature_names = (FEATURES_NUMERIC
                     + list(best.named_steps["pre"]
                            .named_transformers_["cat"]["onehot"]
                            .get_feature_names_out(FEATURES_CATEGORICAL)))
    clf = best.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        importance = clf.feature_importances_
        kind = "Gini importance"
    else:
        importance = np.abs(clf.coef_[0])
        kind = "absolute coefficient"
    imp = (pd.DataFrame({"feature": feature_names, "importance": importance})
           .sort_values("importance", ascending=False).reset_index(drop=True))

    # --- Score every delivered order so Power BI can show risk.
    risk = pd.DataFrame({
        "order_id": df["order_id"],
        "late_risk": best.predict_proba(X)[:, 1],
        "is_late_actual": y,
        "in_test_period": df.index.isin(test_idx).astype(int),
    })
    risk["risk_band"] = pd.cut(risk["late_risk"], [-0.01, 0.25, 0.5, 0.75, 1.0],
                               labels=["Low", "Medium", "High", "Very High"])

    summary = {
        "metrics": metrics, "best_model": best_name, "importance": imp,
        "split_date": str(split_date.date()), "n_train": len(train_idx),
        "n_test": len(test_idx), "late_rate": float(y.mean()),
        "feature_kind": kind,
    }
    return risk, summary


def write_ml_report(summary: dict) -> None:
    """Write docs/ml_report.md with metrics, the decision, and the honest limitations."""
    if not summary:
        return

    m = summary["metrics"]
    lines = [
        "# Late-delivery risk model", "",
        "**Question:** at the moment an order is placed, how likely is it to arrive after "
        "the promised date?", "",
        f"- Training data: {summary['n_train']:,} orders placed before {summary['split_date']}",
        f"- Test data: {summary['n_test']:,} orders placed after that date "
        "(a time-based split, so the model never sees the future)",
        f"- Overall late rate: {summary['late_rate']:.1%}", "",
        "## Results", "",
        "| Model | ROC-AUC | PR-AUC | Baseline (always-late rate) |", "|---|---|---|---|",
    ]
    for name, values in m.items():
        lines.append(f"| {name} | {values['roc_auc']:.3f} | {values['pr_auc']:.3f} "
                     f"| {values['baseline_rate']:.3f} |")

    best = summary["best_model"]
    lines += ["", f"**Selected model: {best}** (chosen on PR-AUC, which is the honest "
                  "metric when the positive class is rare — ROC-AUC looks flattering on "
                  "imbalanced data).", "",
              "### Classification report (test period)", "", "```",
              m[best]["report"].rstrip(), "```", "",
              "### Confusion matrix (rows = actual, columns = predicted)", "",
              "| | Predicted on time | Predicted late |", "|---|---|---|",
              f"| **Actually on time** | {m[best]['confusion'][0][0]:,} | {m[best]['confusion'][0][1]:,} |",
              f"| **Actually late** | {m[best]['confusion'][1][0]:,} | {m[best]['confusion'][1][1]:,} |",
              "",
              "## What drives late delivery", "",
              f"Top 15 features by {summary['feature_kind']}:", "",
              "| # | Feature | Importance |", "|---|---|---|"]
    for i, r in summary["importance"].head(15).iterrows():
        lines.append(f"| {i + 1} | `{r['feature']}` | {r['importance']:.4f} |")

    lines += ["", "## How this is used", "",
              "`outputs/model/fact_order_risk.csv` holds a predicted probability and a risk "
              "band for every delivered order. Power BI joins it to Fact_Orders on order_id, "
              "giving the report an at-risk view alongside the historical pages.", "",
              "## Limitations (say these before an interviewer asks)", "",
              "- Observational data: the model finds association, not cause.",
              "- Only order-time features are used. Carrier scans and warehouse dispatch "
              "times would likely improve it a lot, but they aren't in this dataset.",
              "- The model is trained on one marketplace in one country over two years; it "
              "would need retraining elsewhere.",
              "- A 0.5 threshold is arbitrary. In production you'd set it from the cost of "
              "a missed late order versus the cost of a false alarm."]

    io_utils.write_markdown(lines, "ml_report.md")
