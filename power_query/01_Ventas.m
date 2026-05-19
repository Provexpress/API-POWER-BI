// QUERY: Ventas
// Lee ventas desde el CSV publicado por el ETL.

let
    FolderUrl = if Text.EndsWith(BaseURL, "/") then BaseURL else BaseURL & "/",
    Files = SharePoint.Files(SharePointSite, [ApiVersion = 15]),
    File = Table.SelectRows(
        Files,
        each [Name] = "ventas.csv"
            and Text.Lower(Uri.UnescapeDataString([Folder Path])) = Text.Lower(Uri.UnescapeDataString(FolderUrl))
    ),
    FileContent = if Table.IsEmpty(File) then error "No se encontro ventas.csv en " & FolderUrl else File{0}[Content],
    Source = Csv.Document(
        FileContent,
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
