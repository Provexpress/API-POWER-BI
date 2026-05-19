// QUERY: Clientes Sectores
// Lee clientes y sectores desde el CSV publicado por el ETL.

let
    FolderUrl = if Text.EndsWith(BaseURL, "/") then BaseURL else BaseURL & "/",
    Files = SharePoint.Files(SharePointSite, [ApiVersion = 15]),
    File = Table.SelectRows(
        Files,
        each [Name] = "clientes_sectores.csv"
            and Text.Lower(Uri.UnescapeDataString([Folder Path])) = Text.Lower(Uri.UnescapeDataString(FolderUrl))
    ),
    FileContent = if Table.IsEmpty(File) then error "No se encontro clientes_sectores.csv en " & FolderUrl else File{0}[Content],
    Source = Csv.Document(
        FileContent,
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
