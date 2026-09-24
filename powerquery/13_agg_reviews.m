// Staging (disable load). Changes grain: reviews -> one row per order.
// Rule: keep the most recently answered review when an order has several.
let
    Source = stg_reviews,
    Grouped = Table.Group(Source, {"order_id"}, {
        {"ReviewScore", each Table.Max(_, "review_answer_timestamp")[review_score], Int64.Type},
        {"ReviewCount", each Table.RowCount(_), Int64.Type}
    })
in
    Grouped
