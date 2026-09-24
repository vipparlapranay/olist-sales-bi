"""Olist sales analytics package.

Modules, in the order the pipeline uses them:
    config     paths and business rules
    io_utils   loading, saving, logging
    validate   data quality checks and scorecard
    transform  star schema (dimensions and two fact tables)
    kpis       independent KPI calculation for reconciliation
    analysis   ABC classification, RFM segmentation, significance testing
    ml         late-delivery risk model
    viz        charts for the README
    pipeline   command-line entry point
"""

__version__ = "1.0.0"
