// FACT (load). One row per order item: revenue, product and seller analysis.
// Order-level fields (IsLate, ReviewScore) are copied down on purpose so you can
// analyse satisfaction by category. Explain this denormalisation in interviews.
let
    Source = stg_order_items,

    MergeOrders = Table.NestedJoin(Source, {"order_id"}, Fact_Orders, {"order_id"}, "O", JoinKind.LeftOuter),
    ExpOrders = Table.ExpandTableColumn(MergeOrders, "O",
        {"customer_id", "order_status", "OrderDate", "IsDelivered", "IsLate", "ReviewScore", "IsValidOrder"},
        {"customer_id", "order_status", "OrderDate", "IsDelivered", "IsLate", "ReviewScore", "IsValidSale"}),

    AddLineTotal = Table.AddColumn(ExpOrders, "LineTotal", each [price] + [freight_value], type number),

    Removed = Table.RemoveColumns(AddLineTotal, {"shipping_limit_date"}),

    Typed = Table.TransformColumnTypes(Removed, {
        {"customer_id", type text}, {"order_status", type text}, {"OrderDate", type date},
        {"IsDelivered", Int64.Type}, {"IsLate", Int64.Type}, {"ReviewScore", Int64.Type},
        {"IsValidSale", Int64.Type}
    })
in
    Typed
