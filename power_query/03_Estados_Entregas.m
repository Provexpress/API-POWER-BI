// QUERY: Estados Entregas
// Lee estados de entregas desde el CSV publicado por el ETL.

let
    Source = Csv.Document(
        Web.Contents(BaseURL & "estados_entregas.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Numero", Int64.Type},
        {"Valor_Mercancia", type number},
        {"Estado", type text},
        {"Empresa", type text},
        {"Identificacion", type text},
        {"Grupo_Personal", type text},
        {"Nombre_Empleado", type text}
    }),
    #"Split Column by Delimiter" = Table.SplitColumn(
        #"Changed Type", "Fecha",
        Splitter.SplitTextByDelimiter("T", QuoteStyle.Csv),
        {"Fecha.1", "Fecha.2"}
    ),
    #"Changed Type1" = Table.TransformColumnTypes(#"Split Column by Delimiter", {
        {"Fecha.1", type date},
        {"Fecha.2", type time}
    }),
    #"Removed Columns" = Table.RemoveColumns(#"Changed Type1", {"Fecha.2"})
in
    #"Removed Columns"
