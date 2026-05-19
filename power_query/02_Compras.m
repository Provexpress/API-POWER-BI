// QUERY: Compras
// Lee compras desde el CSV publicado por el ETL.

let
    Source = Csv.Document(
        Web.Contents("https://provexpress-my.sharepoint.com/personal/especialista_preventa_provexpress_com_co/Documents/PowerBI/Proveexpress/compras.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Identificacion", type text},
        {"Empresa", type text},
        {"Prefijo", type text},
        {"Codigo_Producto", type text},
        {"Producto", type text},
        {"Categoria", type text},
        {"SubCategoria", type text},
        {"Marca", type text},
        {"Numero", Int64.Type},
        {"Unidades", Int64.Type},
        {"Valor_Mercancia", Currency.Type}
    })
in
    #"Changed Type"
