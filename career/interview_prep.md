# Interview prep for this project

Practise answering these out loud in under 90 seconds each. Adapt the model answers
into your own words; don't memorise them.

## The 2-minute walkthrough (you'll be asked this every time)

Structure: **problem → data → what I built → one insight → what I'd improve.**

> "I built a sales dashboard for an e-commerce marketplace using a public dataset of
> about [100k] orders across nine tables. The goal was to answer five commercial
> questions, like which categories drive revenue and whether late delivery hurts
> satisfaction. I profiled the data first and found a few traps, like customer ID
> changing with every order. I modelled it as a star schema with two fact tables, wrote
> about [30] DAX measures, added row-level security, and reconciled every KPI against
> a pandas script. The strongest finding was that late orders scored [__] vs [__] for
> on-time orders. Next I'd add dynamic security and a seller performance page."

## Technical questions

**Why two fact tables instead of one?**
Revenue lives at item level; delivery and reviews live at order level. One table at item
grain would repeat an order's delivery time once per item, inflating averages. Two facts
at their natural grain, sharing dimensions, keeps every metric correct.

**What's a star schema and why use it?**
Facts hold measurable events (sales); dimensions hold descriptive attributes (product,
customer, date). Filters flow one way from dimensions to facts. It's simpler for users,
faster for the VertiPaq engine, and makes DAX behave predictably.

**Measure vs calculated column?**
A calculated column is computed at refresh, stored per row and uses memory. A measure is
computed at query time in the current filter context. Aggregations like revenue belong
in measures; row-level attributes used for slicing (like IsLate) belong upstream in
Power Query or as columns.

**Why did you calculate IsLate in Power Query rather than DAX?**
It's a row-level attribute that never changes with filters. Computing it once at refresh
is cheaper and keeps measures simple.

**Explain CALCULATE.**
It evaluates an expression in a modified filter context. For example,
`CALCULATE([Revenue], SAMEPERIODLASTYEAR(Dim_Date[Date]))` shifts the date filter back a
year and recomputes revenue.

**Why ALLSELECTED in your ranking measure?**
ALL would rank against every category and ignore slicers. ALLSELECTED removes the
category filter from the current row but keeps the user's slicer selections, so ranks
reflect what they've selected (for example, top categories within one region).

**Why must the date table be marked?**
Time-intelligence functions need a continuous date column with no gaps. Marking it tells
Power BI to use that table for functions like SAMEPERIODLASTYEAR and TOTALMTD.

**How does your row-level security work?**
A role filters Dim_Customer by region; that filter propagates to both facts through
single-direction relationships. In production I'd use dynamic RLS with a user-to-region
mapping table and USERPRINCIPALNAME().

**How did you make sure the numbers were right?**
I wrote a pandas script that independently recalculates each KPI from the raw CSVs using
the same business rules, then compared it with the dashboard. I also documented ten test
cases, such as confirming cancelled orders are excluded.

**What data quality problems did you find?**
Customer ID changes per order, reviews have duplicates, orders can have several payment
rows, some categories lack translations, zip codes lose leading zeros if typed as numbers,
and the first and last months are incomplete.

## Behavioural question you can answer with this project

**"Tell me about a time you found a problem in data."**
Situation: counting customers. Task: report active customers accurately. Action: profiling
showed customer_id had as many distinct values as orders, which made no sense for repeat
buyers; I found customer_unique_id and switched the measure to it. Result: the customer
count was [__] rather than [__], and I documented the rule in the KPI dictionary.
