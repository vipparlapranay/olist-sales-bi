# Connecting Power BI to the pipeline output

The Python pipeline has already done the cleaning, the grain fixes and the modelling.
Power BI's job now is presentation, DAX and interactivity, which is how modern BI teams
actually split the work.

**You no longer need the staging scripts in `powerquery/`.** Keep them in the repo — they
show you can do the same transformations in Power Query, and some employers still work
that way — but for building the report, follow this file instead.

## 1. Load the tables

1. Open Power BI Desktop → **Get data → Text/CSV**.
2. Load each file from `outputs/model/`:

| File | Loads as | Notes |
|---|---|---|
| `fact_sales.csv` | fact_sales | one row per order item |
| `fact_orders.csv` | fact_orders | one row per order |
| `dim_date.csv` | dim_date | continuous calendar |
| `dim_customer.csv` | dim_customer | |
| `dim_product.csv` | dim_product | |
| `dim_seller.csv` | dim_seller | |
| `dim_category_abc.csv` | dim_category_abc | A/B/C class per category |
| `dim_customer_segment.csv` | dim_customer_segment | RFM scores and segment labels |
| `fact_order_risk.csv` | fact_order_risk | predicted late risk per order |

**Don't rename the queries.** Power BI names each one after its file, which is already
the name every measure in `dax/01_measures.dax` expects. Renaming to `Fact_Sales` while
the columns stay lowercase gives you a model that is half one convention and half the
other, and every measure then has to be edited to match.

Faster alternative: **Get data → Folder**, point at `outputs/model`, and Power BI will
list every CSV at once.

## 2. Check the data types

Power BI usually guesses well here because the pipeline writes clean files, but confirm:
- `date` in dim_date is **Date**
- `order_date` in both fact tables is **Date**
- `price`, `freight_value`, `line_total`, `monetary` are **Decimal Number**
- Zip prefix columns are **Text** (leading zeros matter)

## 3. Build the relationships

| From (one) | To (many) | Cross-filter |
|---|---|---|
| dim_date[date] | fact_sales[order_date] | Single |
| dim_date[date] | fact_orders[order_date] | Single |
| dim_customer[customer_id] | fact_sales[customer_id] | Single |
| dim_customer[customer_id] | fact_orders[customer_id] | Single |
| dim_product[product_id] | fact_sales[product_id] | Single |
| dim_seller[seller_id] | fact_sales[seller_id] | Single |
| dim_category_abc[category] | dim_product[category] | Single |
| fact_orders[order_id] | fact_order_risk[order_id] | Single (1:1) |
| dim_customer_segment[customer_unique_id] | dim_customer[customer_unique_id] | Single |

Then:
- **Mark dim_date as a date table** (Table tools → Mark as date table → `date`).
- Sort `month` by `month_no`, and `year_month` by `year_month_sort`.
- Hide foreign keys on the fact tables.
- Set `customer_state_name` and `seller_state_name` data category to **State or Province**.

The last three relationships are why the analysis pays off: ABC class, customer segment
and predicted risk all become slicers in the report without any extra DAX.

## 4. Add the measures

Paste from `dax/01_measures.dax` as before. Two small differences now that the pipeline
built the tables:

- Column names are lower case with underscores, e.g. `fact_sales[price]`,
  `fact_sales[is_valid_sale]`, `fact_orders[is_late]`, `fact_orders[review_score]`.
- `dim_date` already exists as a table, so skip `dax/00_date_table.dax`.

Three extra measures worth adding, since you now have data the DAX file didn't know about:

```
Avg Late Risk = AVERAGE ( fact_order_risk[late_risk] )

High Risk Orders =
CALCULATE ( COUNTROWS ( fact_order_risk ), fact_order_risk[risk_band] IN { "High", "Very High" } )

Class A Revenue =
CALCULATE ( [Revenue], dim_category_abc[abc_class] = "A" )
```

## 5. Extra report pages you can now build

- **Category strategy** — slice any page by ABC class; show class A, B and C revenue side
  by side with their average review scores.
- **Customer segments** — revenue and customer count by RFM segment; highlight
  "At Risk (high value)" as the group worth winning back.
- **Delivery risk** — orders by risk band, predicted vs actual late rate, and the top
  drivers from `docs/ml_report.md`.

## 6. Refreshing

Re-run `python -m olist.pipeline all`, then hit **Refresh** in Power BI. The file paths
don't change, so the report picks up the new data.

**Worth saying in an interview:** "The Python pipeline is the single source of truth for
business logic, with unit tests and data quality checks. Power BI consumes curated tables
rather than reimplementing rules in DAX, so there's one definition of revenue, not two."
