// QUERY: Clientes Sectores
// Lee clientes y sectores desde el CSV publicado por el ETL.

let
    Source = Csv.Document(
        Web.Contents(BaseURL & "clientes_sectores.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Identificacion", type text},
        {"Nombre_Empleado", type text},
        {"Empresa", type text},
        {"Estado", type text},
        {"Industria", type text},
        {"Clasificacion_Cliente", type text}
    })
in
    #"Changed Type"
