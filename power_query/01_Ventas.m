// QUERY: Ventas
// Lee ventas desde el CSV publicado por el ETL.

let
    Source = Csv.Document(
        Web.Contents(BaseURL & "ventas.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Fecha_Emision", type date},
        {"Numero", Int64.Type},
        {"Nombre_Empleado", type text},
        {"Identificacion", type text},
        {"Empresa", type text},
        {"Prefijo", type text},
        {"Codigo_Producto", type text},
        {"Producto", type text},
        {"Categoria", type text},
        {"SubCategoria", type text},
        {"Marca", type text},
        {"Valor_Mercancia", type number},
        {"Unidades", Int64.Type}
    }),
    #"Renamed Columns" = Table.RenameColumns(#"Changed Type", {
        {"Nombre_Empleado", "Vendedor"},
        {"Valor_Mercancia", "Venta"}
    })
in
    #"Renamed Columns"
