// Staging (disable load). One row per order.
let
    Source = fnLoadCsv("olist_orders_dataset.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"order_id", type text},
        {"customer_id", type text},
        {"order_status", type text},
        {"order_purchase_timestamp", type datetime},
        {"order_approved_at", type datetime},
        {"order_delivered_carrier_date", type datetime},
        {"order_delivered_customer_date", type datetime},
        {"order_estimated_delivery_date", type datetime}
    }, "en-US")
in
    Typed
