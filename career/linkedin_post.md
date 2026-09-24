# LinkedIn post (Day 8)

Attach 2 screenshots: the Executive page and the Delivery page. Post Tuesday to Thursday,
morning Melbourne time. Reply to every comment in the first hour.

---

I just finished a Power BI project analysing [100k+] orders from Olist, a Brazilian
online marketplace. 📊

The question I found most interesting: **does late delivery actually hurt customer
satisfaction?**

It does, a lot. Orders that arrived late averaged a review score of [__] out of 5,
compared with [__] for on-time orders. [Worst state] had the highest late-delivery rate
at [__]%.

A few other findings:
→ The top [__] product categories drive [__]% of revenue
→ [Region] accounts for [__]% of all sales
→ [One more finding]

What I built:
• A star schema with two fact tables at order and item grain, so delivery metrics
  aren't double-counted across items
• [30+] DAX measures: YoY growth, rolling averages, dynamic ranking, Pareto analysis
• Row-level security by region
• Every KPI reconciled against an independent Python calculation

The trickiest part was realising the customer ID in this dataset changes with every
order, so counting real customers needed a different key entirely. Good reminder to
profile the data before trusting it.

Code, DAX and documentation: [GitHub link]

I'm currently looking for Data Analyst, BI Analyst and Data Engineer roles in Melbourne.
Happy to walk anyone through the build.

#PowerBI #DataAnalytics #DAX #BusinessIntelligence #DataAnalyst #Melbourne
