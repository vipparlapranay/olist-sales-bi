# Row-level security and validation (Day 6)

## Part A: Row-level security

**Goal:** a regional manager opening the report sees only their region's customers.

1. **Modeling → Manage roles → New role.** Name it `Southeast Manager`.
2. Select table **Dim_Customer** and enter the DAX filter:
   ```
   [Customer Region] = "Southeast"
   ```
3. Repeat for the other regions: North, Northeast, Center-West, South.
4. **Modeling → View as → Southeast Manager.** Every page should now show Southeast only.
   Screenshot this for your README.

**Why it works:** the filter on Dim_Customer flows down the one-to-many relationships to
*both* fact tables, so revenue, delivery and review measures are all restricted.

**What to say in interviews:** "This is static RLS: one role per region. In production
I'd use dynamic RLS: a security table mapping each user's email to their region, filtered
with `USERPRINCIPALNAME()`, so adding a manager is a data change, not a model change."

**Optional stretch (dynamic RLS):**
1. Enter data → table `Security_Users` with columns `Email`, `Region`.
2. Relate `Security_Users[Region]` to `Dim_Customer[Customer Region]`
   (many-to-many, single direction from Security_Users to Dim_Customer).
3. Role `Dynamic Region` on Security_Users: `[Email] = USERPRINCIPALNAME()`.
4. Test with View as → Other user → enter an email from your table.

## Part B: Performance

1. **View → Performance Analyzer → Start recording → Refresh visuals.**
2. Sort by duration. Anything over ~1 second: check for measures using FILTER over large
   tables, too many visuals, or high-cardinality columns in slicers.
3. Record the slowest visual before and after your fix. That's a concrete interview story.

## Part C: Validation (reconciliation)

Numbers you can't prove are numbers nobody trusts. Reconcile the dashboard against an
independent calculation.

1. From the repo root run: `python scripts/reconcile.py`
2. It writes `docs/reconciliation_expected.md` with the expected value for each KPI.
3. In Power BI, clear all slicers, put each measure on a card, and fill in the
   Power BI column. They should match exactly (or to rounding).
4. If a number doesn't match, investigate. Common causes are listed below.

| Symptom | Likely cause |
|---|---|
| Revenue too high | Payments joined at item grain (duplication), or cancelled orders included |
| Customers too high | Counting customer_id instead of customer_unique_id |
| Late % different | Comparing datetimes instead of dates, or including undelivered orders |
| Avg review different | Duplicate reviews not reduced to one per order |
| YoY blank | Dim_Date not marked as date table, or relationship missing |

## Part D: Test cases

| ID | Test | Steps | Expected | Actual | Pass? |
|---|---|---|---|---|---|
| T01 | Revenue matches source | Compare card to reconcile.py | Equal | [ ] | [ ] |
| T02 | Orders matches source | Compare card to reconcile.py | Equal | [ ] | [ ] |
| T03 | Customers uses unique IDs | Compare card to reconcile.py | Equal | [ ] | [ ] |
| T04 | Cancelled orders excluded | Filter order_status = canceled on a table visual | Revenue blank | [ ] | [ ] |
| T05 | Late % matches source | Compare card to reconcile.py | Equal | [ ] | [ ] |
| T06 | Top 10 shows 10 categories | Check Top 10 bar chart | 10 bars | [ ] | [ ] |
| T07 | Category ranks respond to slicers | Select one region | Ranks recalculate | [ ] | [ ] |
| T08 | RLS restricts data | View as Southeast Manager | Only Southeast states | [ ] | [ ] |
| T09 | YoY % correct for one month | Hand-calculate one month vs the same month last year | Equal | [ ] | [ ] |
| T10 | Drill-through works | Right-click a category → Drill through | Detail page filtered | [ ] | [ ] |
