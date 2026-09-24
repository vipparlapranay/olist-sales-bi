// DIMENSION (load). One row per seller.
let
    Source = stg_sellers,
    MergeStates = Table.NestedJoin(Source, {"seller_state"}, Ref_States, {"StateCode"}, "S", JoinKind.LeftOuter),
    ExpStates = Table.ExpandTableColumn(MergeStates, "S", {"StateName", "Region"}, {"Seller State Name", "Seller Region"}),
    ProperCity = Table.TransformColumns(ExpStates, {{"seller_city", Text.Proper, type text}}),
    Renamed = Table.RenameColumns(ProperCity, {
        {"seller_city", "Seller City"},
        {"seller_state", "Seller State"},
        {"seller_zip_code_prefix", "Seller Zip Prefix"}
    })
in
    Renamed
