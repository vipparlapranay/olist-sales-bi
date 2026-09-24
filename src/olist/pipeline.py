"""
pipeline.py — the command-line entry point that runs everything.

USAGE (from the repo root)
--------------------------
    python -m olist.pipeline all         # the whole thing, start to finish
    python -m olist.pipeline validate    # data quality checks only
    python -m olist.pipeline build       # star schema -> outputs/model/
    python -m olist.pipeline analyse     # ABC, RFM, significance test
    python -m olist.pipeline ml          # late-delivery risk model
    python -m olist.pipeline all --strict --verbose

WHY A CLI INSTEAD OF A NOTEBOOK
-------------------------------
Notebooks are great for exploring and terrible for repeating. A pipeline with named
stages can be re-run, scheduled, tested and put in CI. When an interviewer asks how you'd
productionise your analysis, this file is the answer: stages, logging, exit codes, and
config separated from logic.
"""
from __future__ import annotations

import argparse
import logging
import sys

from . import analysis, config, io_utils, kpis, ml, transform, validate, viz

log = logging.getLogger("olist.pipeline")


def stage_validate(frames, strict: bool):
    """Stage 1 — check the raw data before trusting any of it."""
    with io_utils.stage("validate"):
        return validate.run(frames, strict=strict)


def stage_build(frames):
    """Stage 2 — build the star schema and write it for Power BI."""
    with io_utils.stage("build star schema"):
        model = transform.build_star_schema(frames)
        for name, table in model.items():
            io_utils.save_table(table, name)

    with io_utils.stage("reconcile KPIs"):
        kpis.write_reconciliation(model)
        monthly = kpis.monthly_revenue(model)
        io_utils.save_table(monthly, "agg_monthly_revenue")
        viz.plot_revenue_trend(monthly)
    return model


def stage_analyse(model):
    """Stage 3 — the analyses that make this more than a chart exercise."""
    with io_utils.stage("analyse"):
        abc = analysis.category_abc(model)
        rfm = analysis.rfm_segments(model)
        test = analysis.delivery_satisfaction_test(model)

        # These two tables are joined into the Power BI model as extra dimensions.
        io_utils.save_table(abc, "dim_category_abc")
        io_utils.save_table(rfm, "dim_customer_segment")

        analysis.write_analysis_report(abc, rfm, test)
        viz.plot_pareto(abc)
        viz.plot_review_by_delivery(model)
    return abc, rfm, test


def stage_ml(model):
    """Stage 4 — train the late-delivery risk model and export the scores."""
    with io_utils.stage("machine learning"):
        risk, summary = ml.train_and_evaluate(model)
        if risk.empty:
            log.warning("Model stage produced no output")
            return None
        io_utils.save_table(risk, "fact_order_risk")
        ml.write_ml_report(summary)
        viz.plot_feature_importance(summary.get("importance"),
                                    summary.get("feature_kind", "importance"))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="olist.pipeline",
        description="Olist sales analytics pipeline: validate, model, analyse, predict.")
    parser.add_argument("stage", choices=["all", "validate", "build", "analyse", "ml"],
                        help="which stage to run")
    parser.add_argument("--data-dir", default=None,
                        help="folder holding the raw Kaggle CSVs (default: ./data)")
    parser.add_argument("--strict", action="store_true",
                        help="stop the run if any critical data quality check fails")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    io_utils.setup_logging(args.verbose)
    config.ensure_dirs()
    data_dir = config.DATA_DIR if args.data_dir is None else __import__("pathlib").Path(args.data_dir)

    log.info("=" * 70)
    log.info("Olist analytics pipeline | stage: %s | data: %s", args.stage, data_dir)
    log.info("=" * 70)

    try:
        with io_utils.stage("load raw data"):
            frames = io_utils.load_all(data_dir)
    except FileNotFoundError as exc:
        log.error(str(exc))
        return 1

    if args.stage in {"all", "validate"}:
        stage_validate(frames, args.strict)
        if args.stage == "validate":
            return 0

    # Later stages all need the model, so build it regardless of which one was asked for.
    model = stage_build(frames)
    if args.stage == "build":
        return 0

    if args.stage in {"all", "analyse"}:
        stage_analyse(model)
        if args.stage == "analyse":
            return 0

    if args.stage in {"all", "ml"}:
        stage_ml(model)

    log.info("Pipeline finished. Outputs in outputs/, reports in docs/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
