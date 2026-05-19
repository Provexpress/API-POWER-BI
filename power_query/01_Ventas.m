// QUERY: Ventas
// Lee ventas desde el CSV publicado por el ETL.

let
    Source = Csv.Document(
        Web.Contents("https://provexpress-my.sharepoint.com/personal/especialista_preventa_provexpress_com_co/Documents/PowerBI/Proveexpress/ventas.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    DateAliases = {"Fecha_Emision", "Fecha Emision", "Fecha_Emisión", "Fecha Emisión", "FechaEmision", "Fecha"},
    ExistingDateColumn = List.First(List.Select(DateAliases, each List.Contains(Table.ColumnNames(#"Promoted Headers"), _)), null),
    #"Renamed Date Column" =
        if ExistingDateColumn = null or ExistingDateColumn = "Fecha_Emision" then
            #"Promoted Headers"
        else
            Table.RenameColumns(#"Promoted Headers", {{ExistingDateColumn, "Fecha_Emision"}}, MissingField.Ignore),
    #"Parsed Date" = Table.TransformColumns(#"Renamed Date Column", {
        {"Fecha_Emision", each try Date.From(_) otherwise try Date.From(DateTime.FromText(Text.From(_))) otherwise null, type date}
    }),
    #"Changed Type" = Table.TransformColumnTypes(#"Parsed Date", {
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
