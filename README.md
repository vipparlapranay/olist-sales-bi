# Olist E-Commerce Sales Dashboard (Power BI)

> Replace every `[placeholder]` before publishing. Delete this line when done.

A Power BI dashboard analysing [100k+] orders from Olist, a Brazilian online marketplace,
to answer five commercial questions: how sales are trending, which product categories
drive revenue, where customers are, whether late delivery hurts satisfaction, and what a
typical order looks like.

![Executive overview](screenshots/01_executive.png)

## Business questions

1. How is revenue trending, and are we growing year on year?
2. Which categories drive most revenue, and which underperform?
3. Where are our customers, and which regions contribute most?
4. Does late delivery hurt customer satisfaction, and by how much?
5. What does a typical order look like?

## Key insights

- **[Insight 1 headline]** — [one sentence with the number]
- **[Insight 2 headline]** — [one sentence with the number]
- **[Insight 3 headline]** — [one sentence with the number]

Full write-up: [docs/07_insights_template.md](docs/07_insights_template.md)

## Data model

Star schema with **two fact tables at their natural grain** sharing conformed dimensions:
`Fact_Sales` (one row per order item) for revenue and product analysis, and `Fact_Orders`
(one row per order) for delivery, payment and review metrics. This prevents order-level
metrics being double-counted across items.

![Model view](screenshots/model_view.png)

Details: [docs/03_data_model.md](docs/03_data_model.md)

## What I built

- **Power Query ETL** in three layers (staging → aggregation → model), including reducing
  payments and reviews to one row per order to avoid duplication ([powerquery/](powerquery/))
- **[30+] DAX measures** covering time intelligence (YoY, MTD, rolling 3 months), dynamic
  ranking, Pareto analysis and delivery/satisfaction KPIs ([dax/](dax/))
- **Row-level security** by region, tested with View as
- **Reconciliation** of every headline KPI against an independent pandas calculation
  ([scripts/reconcile.py](scripts/reconcile.py))
- A **KPI dictionary** so every number has one agreed definition ([docs/04_kpi_dictionary.md](docs/04_kpi_dictionary.md))

## Report pages

| Page | Purpose |
|---|---|
| Executive overview | Revenue trend, YoY, regional split, order profile |
| Product performance | Top/bottom categories, Pareto concentration |
| Delivery & experience | Late delivery rate and its effect on review scores |
| Category detail | Drill-through for any category |

![Product performance](screenshots/02_products.png)
![Delivery and experience](screenshots/03_delivery.png)

## Data quality issues handled

- `customer_id` is per order, so customers are counted by `customer_unique_id`
- Duplicate reviews reduced to the latest per order
- Multiple payment rows per order aggregated before modelling
- Misspelled source columns renamed; zip prefixes kept as text to preserve leading zeros
- Missing category translations fall back to the Portuguese name, then "Unknown"
- Incomplete first and last months excluded from trend charts

## Tools

Power BI Desktop, Power Query (M), DAX, Python (pandas), Git/GitHub

## How to run

1. Download the dataset from Kaggle ("Brazilian E-Commerce Public Dataset by Olist")
   and place the CSVs in `data/`.
2. Open `olist_sales.pbix`, go to Transform data → Manage parameters, and set
   `DataFolder` to your `data/` path.
3. Refresh.
4. Optional: `pip install pandas`, then `python scripts/reconcile.py` to regenerate
   the expected KPI values.

## Next steps

- Dynamic row-level security with `USERPRINCIPALNAME()`
- Aggregate geolocation to one point per zip prefix for city-level maps
- Seller performance page (late rate and review score by seller)

## Data source

Olist, *Brazilian E-Commerce Public Dataset*, via Kaggle. Raw data isn't included in this
repository; see the Kaggle page for licence terms.
