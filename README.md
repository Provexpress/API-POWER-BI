# Proveexpress - ETL para Power BI

Este proyecto descarga datos de la API externa, genera CSVs y los sube a SharePoint para que Power BI Service pueda refrescar desde HTTPS sin gateway.

## Arquitectura

```text
API externa -> GitHub Actions -> SharePoint -> Power BI Service
```

## Estructura

```text
.github/workflows/daily-refresh.yml  # Action diario y manual
scripts/fetch_data.py                # Descarga datos de la API
scripts/upload_sharepoint.py         # Sube CSVs a SharePoint
power_query/                         # Consultas M para leer los CSVs
.env.example                         # Plantilla local, sin secretos reales
requirements.txt                     # Dependencias Python del workflow
```

## Secrets requeridos en GitHub Actions

Configura estos valores en `Settings > Secrets and variables > Actions > New repository secret`.

| Secret | Uso |
| --- | --- |
| `API_BASE_URL` | URL base de la API externa |
| `API_USERNAME` | Usuario de la API |
| `API_PASSWORD` | Password de la API |
| `AZURE_TENANT_ID` | Tenant ID de Azure AD |
| `AZURE_CLIENT_ID` | Client ID de la App Registration |
| `AZURE_CLIENT_SECRET` | Client secret de la App Registration |

Para localizar la carpeta destino de SharePoint/OneDrive, configura una de estas opciones:

| Secret | Recomendacion |
| --- | --- |
| `SHAREPOINT_FOLDER_URL` | Recomendado para una carpeta compartida. Pega la URL completa de la carpeta |
| `SHAREPOINT_SITE_URL` | Recomendado. Ejemplo: `https://empresa.sharepoint.com/sites/NombreSitio` |
| `SHAREPOINT_SITE_ID` | Alternativa si ya tienes el ID exacto del sitio |
| `SHAREPOINT_SITE` | Alternativa por busqueda o hostname |
| `SHAREPOINT_DRIVE_ID` | Alternativa si ya tienes el ID exacto del drive/biblioteca destino |

`SHAREPOINT_FOLDER` es opcional. Si usas `SHAREPOINT_FOLDER_URL`, se ignora porque la URL ya apunta a la carpeta destino. Si no usas `SHAREPOINT_FOLDER_URL`, sirve como ruta dentro del drive; si se deja vacio, el script usa `PowerBI/Proveexpress`.

## Permisos de Azure

La App Registration debe tener permisos de Microsoft Graph para escribir en el sitio o drive destino. Segun tu politica de seguridad, usa permisos de aplicacion como `Sites.Selected` con asignacion al sitio especifico, `Sites.ReadWrite.All`, o `Files.ReadWrite.All` cuando el destino sea una carpeta de OneDrive empresarial compartida.

## Ejecucion del Action

El workflow corre todos los dias a las 5:00 AM Colombia (`10:00 UTC`) y tambien puede ejecutarse manualmente con `workflow_dispatch`.

El Action hace tres cosas:

1. Valida que los secrets obligatorios existan.
2. Ejecuta `scripts/fetch_data.py` y genera los CSVs en `data/`.
3. Ejecuta `scripts/upload_sharepoint.py` y sube los CSVs a SharePoint.

## Archivos generados

La carpeta destino debe terminar con estos archivos:

```text
ventas.csv
compras.csv
estados_entregas.csv
cotizaciones_estados.csv
clientes_sectores.csv
empleados.csv
```

## Configuracion en Power BI

1. Abre el `.pbix` en Power BI Desktop.
2. Crea el parametro `SharePointSite` con la URL del sitio SharePoint/OneDrive.
3. Crea el parametro `BaseURL` con la URL HTTPS donde quedan los CSVs.
4. Asegurate de que `BaseURL` termine en `/`.
5. Reemplaza las consultas con los archivos de `power_query/`.
6. Publica el reporte y configura la actualizacion programada.

Los parametros deben llamarse exactamente `SharePointSite` y `BaseURL`. Si quedan con otro nombre, por ejemplo `Token`, las consultas no van a usar la URL correcta.
Las consultas usan `SharePoint.Files`, por eso en Power BI Service las credenciales deben configurarse contra el sitio SharePoint/OneDrive como `Organizational account`, sin gateway local.

No subas `.env` ni secretos reales. Si algun secreto real ya se compartio o se subio antes, rota ese secreto en Azure/API y actualizalo en GitHub Actions.
