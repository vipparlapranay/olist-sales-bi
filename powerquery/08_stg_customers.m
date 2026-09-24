// Staging (disable load). Zip prefixes stay TEXT to keep leading zeros.
let
    Source = fnLoadCsv("olist_customers_dataset.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"customer_id", type text},
        {"customer_unique_id", type text},
        {"customer_zip_code_prefix", type text},
        {"customer_city", type text},
        {"customer_state", type text}
    })
in
    Typed
