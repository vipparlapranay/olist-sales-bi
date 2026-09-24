// Staging (disable load). One row per payment line; an order can have several.
let
    Source = fnLoadCsv("olist_order_payments_dataset.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"order_id", type text},
        {"payment_sequential", Int64.Type},
        {"payment_type", type text},
        {"payment_installments", Int64.Type},
        {"payment_value", type number}
    }, "en-US")
in
    Typed
