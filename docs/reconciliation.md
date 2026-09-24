# KPI reconciliation

Values calculated in Python straight from the modelled tables. Open the Power BI report with **all slicers cleared**, put each measure on a card, and fill in the second column. Anything that doesn't match is a bug in one of the two engines.

| KPI | Python (expected) | Power BI (actual) | Match? |
|---|---|---|---|
| Revenue | 13,494,400.74 | | |
| Freight | 2,241,126.29 | | |
| Gross Order Value | 15,735,527.03 | | |
| Orders | 98,199 | | |
| Items Sold | 112,101 | | |
| AOV | 137.42 | | |
| Items per Order | 1.14 | | |
| Customers | 94,983 | | |
| Active Sellers | 3,053 | | |
| Delivered Orders | 96,470 | | |
| Late Orders | 6,534 | | |
| Late Delivery % | 6.8% | | |
| Avg Delivery Days | 12.1 | | |
| Avg Days vs Estimate | -11.9 | | |
| Reviewed Orders | 99,441 | | |
| Avg Review Score | 4.07 | | |
| % 5-Star | 57.4% | | |
| % Detractors | 15.1% | | |
| Avg Review (Late) | 2.26 | | |
| Avg Review (On Time) | 4.28 | | |
| Review Gap (On Time - Late) | 2.02 | | |

## Revenue by year (check the YoY measures)

| Year | Revenue |
|---|---|
| 2016 | 44,726.06 |
| 2017 | 6,108,492.27 |
| 2018 | 7,341,182.41 |

## Monthly revenue

Use this to choose the date range for trend charts: drop the months at each end where order volume collapses, and write the decision in the KPI dictionary.

| Month | Revenue | Orders |
|---|---|---|
| 2016-09 | 207.86 | 2 |
| 2016-10 | 44,507.30 | 290 |
| 2016-12 | 10.90 | 1 |
| 2017-01 | 120,098.27 | 787 |
| 2017-02 | 244,959.35 | 1,718 |
| 2017-03 | 368,341.32 | 2,617 |
| 2017-04 | 353,842.98 | 2,377 |
| 2017-05 | 503,159.19 | 3,640 |
| 2017-06 | 429,916.61 | 3,205 |
| 2017-07 | 492,287.30 | 3,946 |
| 2017-08 | 568,245.79 | 4,272 |
| 2017-09 | 621,415.91 | 4,227 |
| 2017-10 | 660,179.62 | 4,547 |
| 2017-11 | 1,003,862.14 | 7,421 |
| 2017-12 | 742,183.79 | 5,618 |
| 2018-01 | 945,456.29 | 7,187 |
| 2018-02 | 837,895.43 | 6,624 |
| 2018-03 | 981,051.06 | 7,168 |
| 2018-04 | 993,592.98 | 6,919 |
| 2018-05 | 992,871.75 | 6,833 |
| 2018-06 | 863,265.53 | 6,145 |
| 2018-07 | 878,044.27 | 6,233 |
| 2018-08 | 848,860.10 | 6,421 |
| 2018-09 | 145.00 | 1 |
