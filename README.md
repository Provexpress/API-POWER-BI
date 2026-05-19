# Proveexpress - ETL para Power BI

Este proyecto descarga datos de la API externa, genera CSVs y los sube a SharePoint para que Power BI Service pueda refrescar desde HTTPS sin gateway.

## Arquitectura recomendada

```text
API externa -> GitHub Actions -> SharePoint -> Power BI Service
```

El repo tambien conserva el proxy HTTPS para Vercel que ya existia en `api/`, `lib/`, `package.json` y `vercel.json`. Ese camino puede seguir sirviendo como respaldo, pero la correccion principal queda en el flujo de GitHub Actions hacia SharePoint.

## Estructura

```text
.github/workflows/daily-refresh.yml  # Action diario y manual
scripts/fetch_data.py                # Descarga datos de la API
scripts/upload_sharepoint.py         # Sube CSVs a SharePoint
power_query/                         # Consultas M para leer los CSVs
api/                                 # Proxy Vercel existente
lib/                                 # Utilidad compartida del proxy Vercel
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
| `SHAREPOINT_FOLDER` | Opcional. Carpeta destino; por defecto `PowerBI/Proveexpress` |

Para localizar el sitio de SharePoint, configura una de estas opciones:

| Secret | Recomendacion |
| --- | --- |
| `SHAREPOINT_SITE_URL` | Recomendado. Ejemplo: `https://empresa.sharepoint.com/sites/NombreSitio` |
| `SHAREPOINT_SITE_ID` | Alternativa si ya tienes el ID exacto del sitio |
| `SHAREPOINT_SITE` | Alternativa por busqueda o hostname |
| `SHAREPOINT_DRIVE_ID` | Alternativa si ya tienes el ID exacto del drive/biblioteca destino |

Si usas `SHAREPOINT_DRIVE_ID`, el script sube directamente a ese drive y no necesita resolver el sitio.

## Permisos de Azure

La App Registration debe tener permisos de Microsoft Graph para escribir en el sitio o drive destino. Segun tu politica de seguridad, usa permisos de aplicacion como `Sites.Selected` con asignacion al sitio especifico, o `Sites.ReadWrite.All` si la organizacion lo permite.

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
2. Crea el parametro `BaseURL` con la URL HTTPS donde quedan los CSVs.
3. Asegurate de que `BaseURL` termine en `/`.
4. Reemplaza las consultas con los archivos de `power_query/`.
5. Publica el reporte y configura la actualizacion programada.

## Proxy Vercel existente

Para seguir usando el proxy Vercel, configura en Vercel:

| Variable | Uso |
| --- | --- |
| `API_BASE_URL` | URL base de la API externa |
| `API_USERNAME` | Usuario de la API |
| `API_PASSWORD` | Password de la API |
| `PROXY_API_KEY` | Clave opcional para proteger los endpoints |

No subas `.env` ni secretos reales. Si algun secreto real ya se compartio o se subio antes, rota ese secreto en Azure/API y actualizalo en GitHub Actions.
