# KPI dictionary (Day 4 and 7)

Every number on the dashboard is defined here. This is the document that stops two
managers arguing about whose "revenue" is right. The DAX lives in `dax/01_measures.dax`.

| Measure | Business definition | Calculation | Format |
|---|---|---|---|
| Revenue | Value of items sold, excluding shipping, on orders not cancelled or unavailable | Sum of item price where IsValidSale = 1 | R$ #,0 |
| Freight | Shipping charged on valid orders | Sum of freight_value where IsValidSale = 1 | R$ #,0 |
| Gross Order Value | What customers paid for items plus shipping | Revenue + Freight | R$ #,0 |
| Orders | Number of valid orders | Distinct order_id in Fact_Sales where valid | #,0 |
| Items Sold | Number of items on valid orders | Row count of Fact_Sales where valid | #,0 |
| AOV | Average revenue per order | Revenue ÷ Orders | R$ #,0.00 |
| Items per Order | Average basket size | Items Sold ÷ Orders | 0.00 |
| Customers | Distinct real customers who placed a valid order | Distinct customer_unique_id | #,0 |
| Revenue PY | Revenue in the same period last year | SAMEPERIODLASTYEAR | R$ #,0 |
| Revenue YoY % | Growth vs same period last year | (Revenue − PY) ÷ PY | 0.0% |
| Revenue MTD / YTD | Month- and year-to-date revenue | TOTALMTD / TOTALYTD | R$ #,0 |
| Revenue Rolling 3M | Revenue over the last 3 months to the current date | DATESINPERIOD −3 months | R$ #,0 |
| Category Rank | Category position by revenue within current filters | RANKX over ALLSELECTED categories | 0 |
| Revenue Share % | Category's share of revenue within current filters | Revenue ÷ revenue of all selected categories | 0.0% |
| Cumulative Share % | Running share for Pareto analysis | Revenue of categories ≥ this one ÷ total | 0.0% |
| Delivered Orders | Orders delivered to the customer | Count of Fact_Orders where IsDelivered = 1 | #,0 |
| Late Delivery % | Share of delivered orders arriving after the promised date | Late ÷ Delivered | 0.0% |
| Avg Delivery Days | Days from purchase to delivery | Average of DeliveryDays on delivered orders | 0.0 |
| Avg Review Score | Average of latest review per order (1–5) | Average of Fact_Orders[ReviewScore] | 0.00 |
| % 5-Star | Share of reviewed orders scoring 5 | 5-star orders ÷ reviewed orders | 0.0% |
| % Detractors | Share of reviewed orders scoring 1 or 2 | 1–2 star orders ÷ reviewed orders | 0.0% |
| Avg Review (Late) / (On Time) | Satisfaction split by delivery performance | Avg Review filtered by IsLate | 0.00 |
| Active Sellers | Sellers with at least one valid sale | Distinct seller_id where valid | #,0 |

## Definitions you decided (fill in)

| Decision | What you chose and why |
|---|---|
| Trend chart date range | [ ] |
| How "late" is measured (days vs estimate > 0) | [ ] |
| Which review counts when an order has several | Latest by answer timestamp |
| Currency shown (BRL, not converted) | [ ] |
