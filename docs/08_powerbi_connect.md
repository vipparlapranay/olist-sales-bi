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
| `fact_sales.csv` | Fact_Sales | one row per order item |
| `fact_orders.csv` | Fact_Orders | one row per order |
| `dim_date.csv` | Dim_Date | continuous calendar |
| `dim_customer.csv` | Dim_Customer | |
| `dim_product.csv` | Dim_Product | |
| `dim_seller.csv` | Dim_Seller | |
| `dim_category_abc.csv` | Dim_Category_ABC | A/B/C class per category |
| `dim_customer_segment.csv` | Dim_Customer_Segment | RFM scores and segment labels |
| `fact_order_risk.csv` | Fact_Order_Risk | predicted late risk per order |

Rename each query to the table name in the second column (right-click → Rename).

Faster alternative: **Get data → Folder**, point at `outputs/model`, and Power BI will
list every CSV at once.

## 2. Check the data types

Power BI usually guesses well here because the pipeline writes clean files, but confirm:
- `date` in Dim_Date is **Date**
- `order_date` in both fact tables is **Date**
- `price`, `freight_value`, `line_total`, `monetary` are **Decimal Number**
- Zip prefix columns are **Text** (leading zeros matter)

## 3. Build the relationships

| From (one) | To (many) | Cross-filter |
|---|---|---|
| Dim_Date[date] | Fact_Sales[order_date] | Single |
| Dim_Date[date] | Fact_Orders[order_date] | Single |
| Dim_Customer[customer_id] | Fact_Sales[customer_id] | Single |
| Dim_Customer[customer_id] | Fact_Orders[customer_id] | Single |
| Dim_Product[product_id] | Fact_Sales[product_id] | Single |
| Dim_Seller[seller_id] | Fact_Sales[seller_id] | Single |
| Dim_Category_ABC[category] | Dim_Product[category] | Single |
| Fact_Orders[order_id] | Fact_Order_Risk[order_id] | Single (1:1) |
| Dim_Customer_Segment[customer_unique_id] | Dim_Customer[customer_unique_id] | Single |

Then:
- **Mark Dim_Date as a date table** (Table tools → Mark as date table → `date`).
- Sort `month` by `month_no`, and `year_month` by `year_month_sort`.
- Hide foreign keys on the fact tables.
- Set `customer_state_name` and `seller_state_name` data category to **State or Province**.

The last three relationships are why the analysis pays off: ABC class, customer segment
and predicted risk all become slicers in the report without any extra DAX.

## 4. Add the measures

Paste from `dax/01_measures.dax` as before. Two small differences now that the pipeline
built the tables:

- Column names are lower case with underscores, e.g. `Fact_Sales[price]`,
  `Fact_Sales[is_valid_sale]`, `Fact_Orders[is_late]`, `Fact_Orders[review_score]`.
- `Dim_Date` already exists as a table, so skip `dax/00_date_table.dax`.

Three extra measures worth adding, since you now have data the DAX file didn't know about:

```
Avg Late Risk = AVERAGE ( Fact_Order_Risk[late_risk] )

High Risk Orders =
CALCULATE ( COUNTROWS ( Fact_Order_Risk ), Fact_Order_Risk[risk_band] IN { "High", "Very High" } )

Class A Revenue =
CALCULATE ( [Revenue], Dim_Category_ABC[abc_class] = "A" )
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
