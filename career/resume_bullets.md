# Resume bullets (Day 8)

Fill in the brackets with your real numbers from the finished dashboard. Pick 2 bullets
per resume; don't use all of them.

## Project header (use on every resume)

**Olist E-Commerce Sales Dashboard** | Power BI, DAX, Power Query, Python | [Month Year]
github.com/vipparlapranay/olist-sales-bi

## For the Data Analyst and BI Analyst resumes

- Designed a star-schema Power BI model with two fact tables at order and item grain
  across [9] source tables and [100k+] orders, preventing double-counting of
  order-level delivery and review metrics.
- Built [30+] DAX measures including year-on-year growth, rolling 3-month revenue,
  dynamic category ranking and Pareto analysis, showing the top [__] categories drive
  [__]% of revenue.
- Quantified the impact of late delivery on satisfaction: late orders averaged a review
  score of [__] vs [__] for on-time orders, across [__]k delivered orders.
- Implemented regional row-level security and reconciled every headline KPI against an
  independent pandas calculation, with [10] documented test cases passing.

## For the Data & Reporting Analyst resume (government/finance angle)

- Delivered an executive reporting pack with a KPI dictionary, documented test cases and
  source reconciliation, so every figure had one agreed definition and was verifiable.

## For the Data Engineer resume (one bullet is enough)

- Built a layered Power Query ETL (staging, aggregation, model) that normalised payment
  and review data to order grain before modelling.

## Skills line additions

Power BI (DAX, Power Query/M, data modelling, star schema, row-level security,
Performance Analyzer), time intelligence, KPI definition, data reconciliation

## Extra bullets from the Python pipeline (Days 1–8 stretch)

Use these on the Data Scientist and Data Engineer resumes especially.

- Built a tested Python analytics pipeline (validate → model → analyse → predict) with a
  22-check data quality framework that scores each load out of 100 and fails the run on
  critical breaches; [18] unit tests running in GitHub Actions.
- Modelled [100k+] orders into a star schema with two fact tables at order and item
  grain, then reconciled every KPI between the Python pipeline and the Power BI report
  to prove both engines agreed.
- Segmented [90k+] customers with RFM scoring, cross-validated against K-Means
  clustering (silhouette [__]), and surfaced the segments as a slicer in the dashboard.
- Quantified the delivery-satisfaction link with a Mann-Whitney U test and Cliff's delta:
  late orders averaged [__] stars vs [__] for on-time, a [__]-star gap.
- Trained a late-delivery risk model on order-time features only, using a time-based
  train/test split to avoid leakage; [best model] reached [__] PR-AUC against a [__]
  base rate, and the per-order risk score feeds an at-risk page in the Power BI report.

## Skills these add

Python (pandas, NumPy, scikit-learn, SciPy, matplotlib), data quality frameworks,
dimensional modelling, RFM segmentation, K-Means clustering, hypothesis testing,
classification modelling, feature engineering, pytest, GitHub Actions CI
