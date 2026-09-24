# Business questions and stakeholder brief (Day 1)

## The brief (pretend a stakeholder sent you this)

> We're the commercial team at an online marketplace. We need a single dashboard our
> leadership can check each week. We want to know how sales are trending, which product
> categories are carrying us and which are dragging, where our customers are, and whether
> delivery problems are hurting customer satisfaction. Regional managers should only see
> their own region.

Writing the brief down first is what real analysts do. It gives every chart a reason to exist.

## The 5 questions the dashboard must answer

| # | Question | Answered on | Key measures |
|---|---|---|---|
| 1 | How is revenue trending, and are we growing year on year? | Executive | Revenue, Revenue YoY %, Rolling 3M |
| 2 | Which categories drive most revenue, and which underperform? Does a small share of categories drive most sales? | Products | Category Rank, Revenue Share %, Cumulative Share % |
| 3 | Where are our customers, and which regions contribute most? | Executive | Revenue by region/state, Customers |
| 4 | Does late delivery hurt customer satisfaction? By how much? | Delivery | Late Delivery %, Avg Review (Late vs On Time) |
| 5 | What does a typical order look like? | Executive | AOV, Items per Order, main payment type |

## Non-functional requirements

- Loads in under 5 seconds per page (check with Performance Analyzer).
- Regional managers see only their region (row-level security).
- Every measure is defined in the KPI dictionary so numbers mean the same thing to everyone.
- Numbers reconcile to the source files (see `06_rls_and_validation.md`).
