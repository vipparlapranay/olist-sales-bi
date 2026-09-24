// Staging (disable load). review_id is NOT unique and some orders have several reviews.
let
    Source = fnLoadCsv("olist_order_reviews_dataset.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"review_id", type text},
        {"order_id", type text},
        {"review_score", Int64.Type},
        {"review_comment_title", type text},
        {"review_comment_message", type text},
        {"review_creation_date", type datetime},
        {"review_answer_timestamp", type datetime}
    }, "en-US")
in
    Typed
