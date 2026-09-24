# Data quality report

**Quality score: 94.6 / 100**  (19 passed, 3 warnings, 0 failures across 22 checks)

Critical checks are weighted 3x warnings. Warnings are known quirks of this dataset that the transform layer handles deliberately.

| Table | Check | Severity | Status | Bad rows | Detail |
|---|---|---|---|---|---|
| orders | `unique_key(order_id)` | critical | **PASS** | 0 | key is unique |
| orders | `not_null(order_id)` | critical | **PASS** | 0 | no nulls |
| orders | `not_null(customer_id)` | critical | **PASS** | 0 | no nulls |
| orders | `not_null(order_status)` | critical | **PASS** | 0 | no nulls |
| orders | `allowed_values(order_status)` | warning | **PASS** | 0 | 8 known values |
| orders | `date_order(order_purchase_timestamp <= order_delivered_customer_date)` | warning | **PASS** | 0 | chronology valid |
| orders | `not_null(order_delivered_customer_date)` | warning | **WARN** | 2,965 | 2,965 null values |
| items | `unique_key(order_id+order_item_id)` | critical | **PASS** | 0 | key is unique |
| items | `non_negative(price)` | critical | **PASS** | 0 | all values >= 0 |
| items | `non_negative(freight_value)` | critical | **PASS** | 0 | all values >= 0 |
| items | `fk(order_id -> order_id)` | critical | **PASS** | 0 | all keys matched |
| items | `fk(product_id -> product_id)` | critical | **PASS** | 0 | all keys matched |
| items | `fk(seller_id -> seller_id)` | critical | **PASS** | 0 | all keys matched |
| payments | `unique_key(order_id+payment_sequential)` | critical | **PASS** | 0 | key is unique |
| payments | `non_negative(payment_value)` | critical | **PASS** | 0 | all values >= 0 |
| reviews | `unique_key(review_id)` | warning | **WARN** | 827 | 827 duplicate keys |
| reviews | `unique_key(order_id)` | warning | **WARN** | 559 | 559 duplicate keys |
| reviews | `allowed_values(review_score)` | critical | **PASS** | 0 | 5 known values |
| customers | `unique_key(customer_id)` | critical | **PASS** | 0 | key is unique |
| products | `unique_key(product_id)` | critical | **PASS** | 0 | key is unique |
| sellers | `unique_key(seller_id)` | critical | **PASS** | 0 | key is unique |
| orders | `fk(customer_id -> customer_id)` | critical | **PASS** | 0 | all keys matched |

## How each warning is handled

- **reviews.unique_key** — review_id repeats and some orders have several reviews. The transform keeps the latest review per order.
- **orders.not_null(order_delivered_customer_date)** — undelivered orders have no delivery date. Delivery metrics only include delivered orders.
- **orders.date_order** — a handful of rows have odd timestamps; they are excluded from delivery-time averages.
