// QUERY: Empleados
// Lee empleados desde el CSV publicado por el ETL.

let
    Source = Csv.Document(
        Web.Contents(BaseURL & "empleados.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Tipo_Personal", type text},
        {"Nombre_Empleado", type text},
        {"Identificacion_Empleado", type text}
    }),
    #"Renamed Columns" = Table.RenameColumns(#"Changed Type", {
        {"Identificacion_Empleado", "Identificacion"}
    })
in
    #"Renamed Columns"
