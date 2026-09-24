// Function: loads one Olist CSV, promotes headers, and turns empty strings into nulls.
// Encoding 65001 = UTF-8 (Portuguese city names have accents).
// QuoteStyle.Csv handles review comments that contain commas and line breaks.
(fileName as text) as table =>
let
    Source = Csv.Document(
        File.Contents(DataFolder & fileName),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    BlanksToNull = Table.TransformColumns(Promoted, {}, each if _ = "" then null else _)
in
    BlanksToNull
