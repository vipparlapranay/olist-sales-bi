# Power Query scripts (Day 2)

## How to use these

1. In Power BI Desktop: **Home → Transform data** to open Power Query.
2. For each file below, in order: **Home → New Source → Blank Query**, then
   **Advanced Editor**, paste the file's contents, click Done, and rename the query to
   the file name (without `.m`).
3. Right-click every query marked *staging* and untick **Enable load**. Staging queries
   feed the model but don't appear in it.
4. **Close & Apply.**

Paste in this order, because later queries reference earlier ones:

| Order | Query | Type | Loads to model? |
|---|---|---|---|
| 1 | DataFolder | Parameter | No |
| 2 | fnLoadCsv | Function | No |
| 3 | Ref_States | Reference | No |
| 4 | stg_orders | Staging | No |
| 5 | stg_order_items | Staging | No |
| 6 | stg_payments | Staging | No |
| 7 | stg_reviews | Staging | No |
| 8 | stg_customers | Staging | No |
| 9 | stg_products | Staging | No |
| 10 | stg_sellers | Staging | No |
| 11 | stg_category_translation | Staging | No |
| 12 | agg_payments | Staging | No |
| 13 | agg_reviews | Staging | No |
| 14 | Fact_Orders | Fact | **Yes** |
| 15 | Fact_Sales | Fact | **Yes** |
| 16 | Dim_Customer | Dimension | **Yes** |
| 17 | Dim_Product | Dimension | **Yes** |
| 18 | Dim_Seller | Dimension | **Yes** |

**First thing to change:** edit `DataFolder` to the full path of your `data/` folder,
ending with a backslash.

The geolocation file isn't used in v1. It has around a million rows with many points per
zip code; a state-level map is enough here. Aggregating it to one point per zip prefix is
a good "next steps" item for your README.

## Pattern worth explaining in interviews

`staging → aggregate → fact/dimension` layering. Staging queries only load and type
data. Aggregation queries change the grain (payments and reviews to one row per order).
Fact and dimension queries shape the final model. Each layer does one job, so when a
number looks wrong you know where to look.
