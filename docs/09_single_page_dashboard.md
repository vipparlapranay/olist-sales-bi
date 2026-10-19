# Single-page dynamic dashboard (Power BI)

Replaces the three static pages with one interactive page. The techniques here — field
parameters, bookmark navigation, dynamic titles, a slide-out filter panel — are what
separate a report that looks built by an analyst from one that looks built by a student.

Every measure referenced below is already in [`dax/01_measures.dax`](../dax/01_measures.dax),
section 9 and 10. Create them first; this file is the layout.

Budget about three hours. Work through in order; each step depends on the one before.

---

## The layout

1280 x 720 canvas, five zones:

```
+---------------------------------------------------------------+
|  OLIST MARKETPLACE ANALYTICS          [= Filters]   [period]   |  header, 60px
+---------------------------------------------------------------+
| Revenue | Orders |  AOV  | Customers | Review | Late %         |  KPI strip, 100px
+---------------------------------------------------------------+
| [Sales] [Products] [Delivery] [Customers] [Risk]               |  view switcher, 40px
+---------------------------------------------------------------+
|                                                                |
|   MAIN CANVAS - contents change with the selected view         |  ~420px
|                                                                |
+---------------------------------------------------------------+
|  Dynamic commentary: one sentence that updates with filters     |  40px
+---------------------------------------------------------------+
```

The slicer panel slides over the main canvas from the right when you press Filters.

---

## Step 1 — Field parameters

A field parameter lets one visual show whichever measure or dimension the user picks.
Without it you need five charts; with it you need one. This is the single technique that
makes the page "dynamic" rather than just tidy.

**Metric switcher.** Modeling → **New parameter** → **Fields**. Name it `Metric`.
Tick from `_Measures`: Revenue, Orders, AOV, Items Sold, Customers, Avg Review Score.
Leave "Add slicer to this page" ticked.

**Dimension switcher.** Modeling → New parameter → Fields. Name it `View By`.
Tick: `dim_date[year_month]`, `dim_product[category]`, `dim_customer[customer_region]`,
`dim_customer[customer_state_name]`, `dim_category_abc[abc_class]`,
`dim_customer_segment[segment]`.

Both appear as tables in the Data pane. Style each slicer as a **dropdown**
(Format → Slicer settings → Options → Style → Dropdown) so they take almost no space.

**Rename the display values** for readability: click the parameter table → Data view →
edit the first column so it reads "Revenue", "Total orders", "Average order value" rather
than raw measure names.

---

## Step 2 — Dynamic titles

Static titles waste the top of every visual. Apply `Main Chart Title` instead:
select the visual → Format pane → General → Title → click the **fx** button next to Text →
Format style **Field value** → choose `Main Chart Title`.

Put `Selected Period Label` in a card, top right of the header.

---

## Step 3 — The KPI strip

Six cards across the top. Use `Revenue Trend Arrow` as a second row under Revenue so the
strip carries a comparison rather than just a number, and colour it with
`Revenue Trend Colour` (Format → Callout value → fx → Field value).

Do this for Revenue, and maybe Orders. Not all six — one or two comparisons read better
than a wall of arrows.

The arrow uses `Revenue YoY % (Like for Like)`, not plain `Revenue YoY %`. The data stops
in August 2018, so a calendar comparison puts twelve months against eight and reports a
fall where there was 138% growth. If an interviewer asks one question about this report,
it will be this one.

---

## Step 4 — The main canvas

Place these on top of each other, occupying the same space. Only one group is visible at
a time, controlled by bookmarks in step 5.

**Group A — Sales** (default view)
- Line chart: `View By` parameter on X-axis, `Metric` parameter on Y-axis
- Bar chart: revenue by `customer_region`

**Group B — Products**
- Bar chart: top 10 categories by the selected metric
- Column chart: metric by `abc_class`
- Scatter: revenue against `Avg Review by Item`, by category

**Group C — Delivery**
- **100% stacked column**: count of orders by `review_score`, legend `Delivery Status`.
  Not a clustered column of raw counts — on-time orders outnumber late ones roughly
  fourteen to one, so a count chart shows a taller on-time bar at every score and
  visually contradicts the finding. The claim is about rates, so plot rates.
- Cards: `Avg Review (Late)` 2.26, `Avg Review (On Time)` 4.28, `Review Gap (On Time - Late)`

**Group D — Customers**
- Bar: `Segment Customers` by `segment`
- Bar: `Segment Value` by `segment`
- Card: `Repeat Customer Rate`

**Group E — Risk**
- Column: `Actual Late Rate` by `risk_band`
- Card: `High Risk Orders`

Use the **Selection pane** (View → Selection) to group each set: select the visuals,
right-click → **Group**. Rename the groups A–E. This is what makes the bookmarks
manageable.

---

## Step 5 — Bookmark navigation

**Create the bookmarks.** View → Bookmarks → Add. For each view:

1. In the Selection pane, show only that group's visuals, hide the rest
2. Bookmarks → Add → rename to "Sales", "Products", and so on
3. Right-click the bookmark → untick **Data** and **Current page**, leave **Display**
   ticked

Unticking Data is the important part: it means switching views doesn't reset the user's
filters.

**Create the buttons.** Insert → Buttons → Blank. Five of them, side by side.
- Style → Text → type the view name
- Action → Type **Bookmark** → select the matching bookmark
- Format the selected state differently (Format → Style → State → On hover / Selected)

---

## Step 6 — Slide-out filter panel

Keeps slicers off the canvas until needed.

1. Insert a rectangle covering the right third of the canvas, give it a background
2. Place your slicers on it: date range, region, category, ABC class, segment
3. Group them all in the Selection pane as "Filter Panel"
4. Create bookmark **Filters Open** with the group visible
5. Create bookmark **Filters Closed** with it hidden
6. Insert → Buttons → add a Filters button in the header, action → bookmark Filters Open
7. Add a small close button on the panel, action → bookmark Filters Closed

Untick **Data** on both bookmarks so opening and closing never changes the filters.

---

## Step 7 — Trim the date range

`dim_date` is built as whole calendar years (Jan 1 to Dec 31) because time intelligence
needs a continuous calendar with no holes. That means it carries months with no sales:
Sep–Dec 2016 at one end, Sep–Dec 2018 at the other.

Any trend visual needs a visual-level filter on `dim_date[date]`, Advanced filtering,
**on or after 01/01/2017** and **on or before 31/08/2018**. Without it the line plunges
to zero at both ends and the chart reads as a collapse rather than an artefact.

Filter on the date column, not on a text month label — a text filter can't express a
range and breaks the moment the data refreshes.

---

## Step 8 — Dynamic commentary

Put the `Commentary` measure in a card at the bottom, left-aligned, small grey text,
word wrap on. It rewrites itself with every interaction, so the written insight never
goes stale against the numbers beside it.

---

## Step 9 — Interaction polish

**Edit interactions.** Select a visual → Format ribbon → **Edit interactions**. Set the
KPI cards to **None** for most visuals, so clicking a bar doesn't blank your headline
numbers unless you want it to.

**Tooltip page.** Insert a new page → Page information → Page size **Tooltip** → tick
"Allow use as tooltip". Put a mini revenue trend on it. Then on your bar charts: Format →
Tooltip → Type **Report page** → select it. Hovering a category now shows its trend.

**Hide the tooltip page** (right-click the tab → Hide page) so the report stays one page.

---

## Step 10 — Before you publish

- [ ] Number formatting is Australian, not Indian — `13,494,400` not `1,34,94,400`.
      This comes from Windows regional format, not Power BI: Settings → Time & language
      → Language & region → Regional format → English (Australia). Restart Power BI.
- [ ] Performance Analyzer: no visual over 1 second
- [ ] Every bookmark has Data unticked
- [ ] Buttons show a clear selected state
- [ ] Alt text on each visual (Format → General → Alt text) — accessibility matters in
      government and enterprise roles, and almost nobody does it
- [ ] Tab order set sensibly (View → Tab order)
- [ ] Theme applied consistently; no default blue left anywhere
- [ ] Mobile layout at least roughly arranged (View → Mobile layout)

---

## What to say about it

> "It's a single page with field parameters so users pick their own metric and dimension,
> bookmark navigation between five analytical views, and a slide-out filter panel.
> Switching views doesn't reset filters, because the bookmarks only capture display state.
> The commentary line is a DAX measure, so the written insight updates with the selection
> rather than going stale."

That covers field parameters, bookmarks, selection state and dynamic DAX in four
sentences, which is more Power BI depth than most junior candidates show in a whole
interview.
