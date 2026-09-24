// FACT (load). One row per order: delivery, payment and review metrics.
let
    Source = stg_orders,

    MergePay = Table.NestedJoin(Source, {"order_id"}, agg_payments, {"order_id"}, "P", JoinKind.LeftOuter),
    ExpPay = Table.ExpandTableColumn(MergePay, "P", {"PaymentValue", "MaxInstallments", "MainPaymentType"}),

    MergeRev = Table.NestedJoin(ExpPay, {"order_id"}, agg_reviews, {"order_id"}, "R", JoinKind.LeftOuter),
    ExpRev = Table.ExpandTableColumn(MergeRev, "R", {"ReviewScore"}),

    AddOrderDate = Table.AddColumn(ExpRev, "OrderDate",
        each DateTime.Date([order_purchase_timestamp]), type date),

    AddIsDelivered = Table.AddColumn(AddOrderDate, "IsDelivered",
        each if [order_status] = "delivered" and [order_delivered_customer_date] <> null then 1 else 0, Int64.Type),

    // Whole days from purchase to delivery (blank if not delivered)
    AddDeliveryDays = Table.AddColumn(AddIsDelivered, "DeliveryDays",
        each if [IsDelivered] = 1
             then Duration.Days([order_delivered_customer_date] - [order_purchase_timestamp])
             else null, Int64.Type),

    // Positive = arrived after the promised date; negative = early
    AddDaysVsEstimate = Table.AddColumn(AddDeliveryDays, "DaysVsEstimate",
        each if [IsDelivered] = 1 and [order_estimated_delivery_date] <> null
             then Duration.Days(DateTime.Date([order_delivered_customer_date]) - DateTime.Date([order_estimated_delivery_date]))
             else null, Int64.Type),

    AddIsLate = Table.AddColumn(AddDaysVsEstimate, "IsLate",
        each if [DaysVsEstimate] <> null and [DaysVsEstimate] > 0 then 1 else 0, Int64.Type),

    AddIsValid = Table.AddColumn(AddIsLate, "IsValidOrder",
        each if List.Contains({"canceled", "unavailable"}, [order_status]) then 0 else 1, Int64.Type),

    Typed = Table.TransformColumnTypes(AddIsValid, {
        {"PaymentValue", type number}, {"MaxInstallments", Int64.Type},
        {"MainPaymentType", type text}, {"ReviewScore", Int64.Type}
    })
in
    Typed
