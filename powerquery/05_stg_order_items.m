// Staging (disable load). One row per item in an order.
let
    Source = fnLoadCsv("olist_order_items_dataset.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"order_id", type text},
        {"order_item_id", Int64.Type},
        {"product_id", type text},
        {"seller_id", type text},
        {"shipping_limit_date", type datetime},
        {"price", type number},
        {"freight_value", type number}
    }, "en-US")
in
    Typed
