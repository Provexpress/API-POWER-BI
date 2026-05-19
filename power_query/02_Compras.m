// QUERY: Compras
// Lee compras desde el CSV publicado por el ETL.

let
    FolderUrl = if Text.EndsWith(BaseURL, "/") then BaseURL else BaseURL & "/",
    SiteUrl = Text.Combine(List.FirstN(Text.Split(Text.TrimEnd(FolderUrl, "/"), "/"), 5), "/"),
    Files = SharePoint.Files(SiteUrl, [ApiVersion = 15]),
    File = Table.SelectRows(
        Files,
        each [Name] = "compras.csv"
            and Text.Lower(Uri.UnescapeDataString([Folder Path])) = Text.Lower(Uri.UnescapeDataString(FolderUrl))
    ),
    FileContent = if Table.IsEmpty(File) then error "No se encontro compras.csv en " & FolderUrl else File{0}[Content],
    Source = Csv.Document(
        FileContent,
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
        {"Valor_Mercancia", type number}
    })
in
    #"Changed Type"
