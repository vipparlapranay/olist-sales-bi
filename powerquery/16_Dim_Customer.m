// DIMENSION (load). One row per customer_id (which is per order in this dataset).
let
    Source = stg_customers,
    MergeStates = Table.NestedJoin(Source, {"customer_state"}, Ref_States, {"StateCode"}, "S", JoinKind.LeftOuter),
    ExpStates = Table.ExpandTableColumn(MergeStates, "S", {"StateName", "Region"}, {"Customer State Name", "Customer Region"}),
    ProperCity = Table.TransformColumns(ExpStates, {{"customer_city", Text.Proper, type text}}),
    Renamed = Table.RenameColumns(ProperCity, {
        {"customer_city", "Customer City"},
        {"customer_state", "Customer State"},
        {"customer_zip_code_prefix", "Customer Zip Prefix"}
    })
in
    Renamed
