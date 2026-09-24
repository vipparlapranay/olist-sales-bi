// Staging (disable load). Fixes the misspelled "lenght" columns from the source file.
let
    Source = fnLoadCsv("olist_products_dataset.csv"),
    Renamed = Table.RenameColumns(Source, {
        {"product_name_lenght", "product_name_length"},
        {"product_description_lenght", "product_description_length"}
    }, MissingField.Ignore),
    Typed = Table.TransformColumnTypes(Renamed, {
        {"product_id", type text},
        {"product_category_name", type text},
        {"product_name_length", Int64.Type},
        {"product_description_length", Int64.Type},
        {"product_photos_qty", Int64.Type},
        {"product_weight_g", Int64.Type},
        {"product_length_cm", Int64.Type},
        {"product_height_cm", Int64.Type},
        {"product_width_cm", Int64.Type}
    }, "en-US")
in
    Typed
