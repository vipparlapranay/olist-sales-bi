# Data profile (Day 1)

Fill in the **Your row count** column yourself by running `scripts/profile_data.py`
or by opening each file. The reference notes below tell you what to look for.

## The 9 tables at a glance

| File | Grain (one row = ...) | Primary key | Your row count | Joins to |
|---|---|---|---|---|
| olist_orders_dataset.csv | one order | order_id | [ ] | customers (customer_id) |
| olist_order_items_dataset.csv | one item within an order | order_id + order_item_id | [ ] | orders, products, sellers |
| olist_order_payments_dataset.csv | one payment instalment/method | order_id + payment_sequential | [ ] | orders |
| olist_order_reviews_dataset.csv | one review | review_id (*not actually unique*) | [ ] | orders |
| olist_customers_dataset.csv | one customer **per order** | customer_id | [ ] | orders |
| olist_products_dataset.csv | one product | product_id | [ ] | order_items |
| olist_sellers_dataset.csv | one seller | seller_id | [ ] | order_items |
| olist_geolocation_dataset.csv | one lat/lng point per zip prefix (many per zip) | none | [ ] | zip prefix (not used in v1) |
| product_category_name_translation.csv | one category | product_category_name | [ ] | products |

## Things you must notice (interviewers love these)

**customer_id vs customer_unique_id.** `customer_id` is created fresh for every order, so it
is really an order-level key. `customer_unique_id` is the actual person. To count real
customers, you must count distinct `customer_unique_id`. Check it yourself: compare the
distinct counts of the two columns.

**Orders and payments are different grains.** One order can have several payment rows
(vouchers plus card, for example). Joining payments directly to items will duplicate
revenue. That's why payments get aggregated to one row per order before modelling.

**Reviews have duplicates.** Some `review_id`s repeat, and some orders have more than one
review. The model keeps the latest review per order.

**Revenue definition.** `price` is what the customer paid for the item. `freight_value`
is shipping. `payment_value` is the total paid per order (items + freight, sometimes
across instalments). Decide your definition once and write it in the KPI dictionary.
This kit uses: **Revenue = sum of item price for orders that aren't cancelled or unavailable.**

**Order status.** Check the distinct values of `order_status`. Cancelled and unavailable
orders shouldn't count as sales.

**Date coverage.** Orders run from late 2016 to late 2018, but the first few months and
the last couple of months are very sparse. Look at order counts by month and decide
which range to show on trend charts. Write your decision down.

**Data quality issues to record:**
- Product columns are misspelled in the source (`product_name_lenght`, `product_description_lenght`).
- Some products have no category, and a few categories are missing from the translation file.
- Zip code prefixes have leading zeros, so they must stay as text, never numbers.
- Delivery dates are blank for orders that were never delivered.
- The translation file may load with a strange first column name (a byte-order mark,
  shown like `ï»¿product_category_name`). Rename it if so.

## Your notes

| Question | Your finding |
|---|---|
| Distinct `customer_id` vs distinct `customer_unique_id` | [ ] |
| Distinct values of `order_status` and their counts | [ ] |
| First and last order date | [ ] |
| Months you'll exclude from trend charts, and why | [ ] |
| Products with no category | [ ] |
| Orders with more than one review | [ ] |
| Orders with more than one payment row | [ ] |
