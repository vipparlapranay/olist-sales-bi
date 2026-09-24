# Report layout (Day 5)

Canvas: 16:9 (1280 × 720). Import the theme first: **View → Themes → Browse for themes →
`theme/olist_theme.json`**. Colour meaning is fixed across the report: blue = revenue,
orange = comparison/prior period, green = good, red = bad.

Layout rules:
- Top-left is the most important number on every page. People read in a Z pattern.
- Every visual has a title that states what it shows, not just the measure name.
- Keep the same slicer panel position on every page and sync slicers (View → Sync slicers).
- Align to a grid: View → Snap to grid. Equal gaps between visuals.
- No more than about 7 visuals per page.
- Restrict trend charts to the date range you chose in the KPI dictionary.

## Page 1 — Executive overview (answers Q1, Q3, Q5)

```
+----------------------------------------------------------------------+
| Title: Sales overview  [period label]         Slicers: Date | Region |
+-----------+-----------+-----------+-----------+----------------------+
| Revenue   | Orders    | AOV       | Customers | Revenue YoY %        |
+-----------+-----------+-----------+-----------+----------------------+
| Line: Revenue by Year Month          | Filled map: Revenue by       |
| + Revenue 3M Monthly Avg (dashed)    | Customer State Name          |
+--------------------------------------+------------------------------+
| Bar: Revenue by Customer Region      | Donut or bar: Orders by      |
|                                      | MainPaymentType              |
+--------------------------------------+------------------------------+
```

## Page 2 — Product performance (answers Q2)

```
+----------------------------------------------------------------------+
| Title: Product performance                    Slicers (synced)       |
+-----------------------------------+----------------------------------+
| Bar: Top 10 categories by Revenue | Bar: Bottom 10 categories        |
| (filter: Is Top 10 Category = 1)  | (filter: Is Bottom 10 = 1)       |
+-----------------------------------+----------------------------------+
| Combo (Pareto): columns = Revenue by Category, sorted desc;          |
| line = Cumulative Share %, with an 80% constant line                 |
+----------------------------------------------------------------------+
| Table: Category | Revenue | Items Sold | Revenue Share % | Category   |
| Rank | Avg Review by Item   (conditional formatting on review)       |
+----------------------------------------------------------------------+
```

## Page 3 — Delivery and customer experience (answers Q4)

```
+----------------------------------------------------------------------+
| Title: Delivery and customer experience       Slicers (synced)       |
+--------------+--------------+--------------+-------------------------+
| Avg Delivery | Late         | Avg Review   | Review Gap              |
| Days         | Delivery %   | Score        | (On Time − Late)        |
+--------------+--------------+--------------+-------------------------+
| Column: Avg Review (On Time) vs      | Line: Late Delivery % by     |
| Avg Review (Late)                    | Year Month                   |
+--------------------------------------+------------------------------+
| Bar: Late Delivery % by Customer State (sorted desc)                 |
+----------------------------------------------------------------------+
```

## Page 4 — Category detail (drill-through, hidden)

Add `Dim_Product[Category]` to the drill-through well. Show: KPI cards for the selected
category, revenue trend, top 10 sellers by revenue, review score distribution (count of
orders by ReviewScore). Add a back button. Hide the page tab.

## Page 5 — Trend tooltip (optional)

Page size: Tooltip. A small line chart of Revenue by Year Month. In Page information,
turn on "Allow use as tooltip", then set it as the report-page tooltip on the Page 2 bar charts.

## Checklist

- [ ] Theme applied
- [ ] Each page answers at least one business question
- [ ] Titles describe the insight area, and dynamic titles use the label measures
- [ ] Slicers synced across pages 1–3
- [ ] Drill-through works from the Top 10 chart
- [ ] Performance Analyzer: no visual slower than ~1 second
