// DIMENSION (load). Adds a clean English "Category" with fallbacks:
// English name -> Portuguese name -> "Unknown".
let
    Source = stg_products,
    MergeTrans = Table.NestedJoin(Source, {"product_category_name"}, stg_category_translation, {"product_category_name"}, "T", JoinKind.LeftOuter),
    ExpTrans = Table.ExpandTableColumn(MergeTrans, "T", {"product_category_name_english"}, {"category_en"}),
    AddCategory = Table.AddColumn(ExpTrans, "Category",
        each let raw = if [category_en] <> null then [category_en] else [product_category_name]
             in if raw = null then "Unknown" else Text.Proper(Text.Replace(raw, "_", " ")),
        type text),
    Removed = Table.RemoveColumns(AddCategory, {"category_en"})
in
    Removed
