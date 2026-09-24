# Late-delivery risk model

**Question:** at the moment an order is placed, how likely is it to arrive after the promised date?

- Training data: 77,176 orders placed before 2018-05-26
- Test data: 19,294 orders placed after that date (a time-based split, so the model never sees the future)
- Overall late rate: 6.8%

## Results

| Model | ROC-AUC | PR-AUC | Baseline (always-late rate) |
|---|---|---|---|
| Logistic Regression | 0.660 | 0.059 | 0.035 |
| Random Forest | 0.644 | 0.055 | 0.035 |

**Selected model: Logistic Regression** (chosen on PR-AUC, which is the honest metric when the positive class is rare — ROC-AUC looks flattering on imbalanced data).

### Classification report (test period)

```
              precision    recall  f1-score   support

           0      0.981     0.545     0.700     18620
           1      0.054     0.714     0.100       674

    accuracy                          0.551     19294
   macro avg      0.518     0.629     0.400     19294
weighted avg      0.949     0.551     0.680     19294
```

### Confusion matrix (rows = actual, columns = predicted)

| | Predicted on time | Predicted late |
|---|---|---|
| **Actually on time** | 10,141 | 8,479 |
| **Actually late** | 193 | 481 |

## What drives late delivery

Top 15 features by absolute coefficient:

| # | Feature | Importance |
|---|---|---|
| 1 | `category_grouped_Audio` | 0.7922 |
| 2 | `category_grouped_Luggage Accessories` | 0.7121 |
| 3 | `same_state` | 0.6489 |
| 4 | `promised_days` | 0.5834 |
| 5 | `category_grouped_Food Drink` | 0.5659 |
| 6 | `category_grouped_Market Place` | 0.5457 |
| 7 | `customer_region_Northeast` | 0.5140 |
| 8 | `customer_region_North` | 0.5071 |
| 9 | `category_grouped_Home Confort` | 0.4869 |
| 10 | `customer_region_Center-West` | 0.4838 |
| 11 | `seller_region_Center-West` | 0.4464 |
| 12 | `customer_region_South` | 0.4273 |
| 13 | `category_grouped_Home Appliances` | 0.3904 |
| 14 | `category_grouped_Bed Bath Table` | 0.3575 |
| 15 | `category_grouped_Office Furniture` | 0.3555 |

## How this is used

`outputs/model/fact_order_risk.csv` holds a predicted probability and a risk band for every delivered order. Power BI joins it to Fact_Orders on order_id, giving the report an at-risk view alongside the historical pages.

## Limitations (say these before an interviewer asks)

- Observational data: the model finds association, not cause.
- Only order-time features are used. Carrier scans and warehouse dispatch times would likely improve it a lot, but they aren't in this dataset.
- The model is trained on one marketplace in one country over two years; it would need retraining elsewhere.
- A 0.5 threshold is arbitrary. In production you'd set it from the cost of a missed late order versus the cost of a false alarm.
