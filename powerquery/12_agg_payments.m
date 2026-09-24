// Staging (disable load). Changes grain: payment lines -> one row per order.
// Without this step, joining payments to orders or items would duplicate values.
let
    Source = stg_payments,
    Grouped = Table.Group(Source, {"order_id"}, {
        {"PaymentValue", each List.Sum([payment_value]), type number},
        {"MaxInstallments", each List.Max([payment_installments]), Int64.Type},
        {"PaymentLines", each Table.RowCount(_), Int64.Type},
        {"MainPaymentType", each Table.Max(_, "payment_value")[payment_type], type text}
    })
in
    Grouped
