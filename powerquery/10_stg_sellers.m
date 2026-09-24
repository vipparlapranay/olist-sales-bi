// Staging (disable load).
let
    Source = fnLoadCsv("olist_sellers_dataset.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"seller_id", type text},
        {"seller_zip_code_prefix", type text},
        {"seller_city", type text},
        {"seller_state", type text}
    })
in
    Typed
