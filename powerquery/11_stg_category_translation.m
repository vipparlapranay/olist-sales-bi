// Staging (disable load). If the first column arrives as "ï»¿product_category_name"
// (a byte-order mark), the rename below fixes it; otherwise it's ignored.
let
    Source = fnLoadCsv("product_category_name_translation.csv"),
    FixBom = Table.RenameColumns(Source, {{"ï»¿product_category_name", "product_category_name"}}, MissingField.Ignore),
    Typed = Table.TransformColumnTypes(FixBom, {
        {"product_category_name", type text},
        {"product_category_name_english", type text}
    })
in
    Typed
