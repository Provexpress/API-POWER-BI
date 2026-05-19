// QUERY: Empleados
// Lee empleados desde el CSV publicado por el ETL.

let
    FolderUrl = if Text.EndsWith(BaseURL, "/") then BaseURL else BaseURL & "/",
    Files = SharePoint.Files(SharePointSite, [ApiVersion = 15]),
    File = Table.SelectRows(
        Files,
        each [Name] = "empleados.csv"
            and Text.Lower(Uri.UnescapeDataString([Folder Path])) = Text.Lower(Uri.UnescapeDataString(FolderUrl))
    ),
    FileContent = if Table.IsEmpty(File) then error "No se encontro empleados.csv en " & FolderUrl else File{0}[Content],
    Source = Csv.Document(
        FileContent,
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
