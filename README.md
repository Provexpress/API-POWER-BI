# 🔌 Proxy HTTPS para Power BI - Provexpress

## ¿Qué es esto?
Una API intermedia en Vercel que actúa como proxy HTTPS entre Power BI Service y la API externa (HTTP).

## Arquitectura
```
API externa (HTTP) → Vercel (HTTPS) → Power BI Service ✅
```

## Endpoints disponibles
| Endpoint Vercel              | Dato              |
|------------------------------|--------------------|
| /api/ventas                  | Ventas             |
| /api/compras                 | Compras            |
| /api/estados-entregas        | Estados Entregas   |
| /api/cotizaciones-estados    | Cotizaciones       |
| /api/clientes-sectores       | Clientes/Sectores  |
| /api/empleados               | Empleados          |

## Pasos para desplegar

### 1. Crear repo en GitHub
- Sube esta carpeta a un repositorio en GitHub

### 2. Conectar con Vercel
- Ve a https://vercel.com
- Importa el repositorio
- En "Environment Variables" agrega:
  - API_BASE_URL = (URL base de la API HTTP)
  - API_USERNAME = (tu usuario)
  - API_PASSWORD = (tu password)
  - PROXY_API_KEY = (inventa una clave segura)

### 3. Deploy
- Vercel despliega automáticamente
- Te da una URL tipo: https://tu-proyecto.vercel.app

### 4. Probar
- Si no configuraste `PROXY_API_KEY`, abre en navegador: https://tu-proyecto.vercel.app/api/ventas
- Si configuraste `PROXY_API_KEY`, prueba enviando el header `x-api-key`
- Debe devolver los datos en JSON

### 5. Actualizar Power BI
- En Power Query, cambia las URLs de HTTP a tu URL de Vercel
- Ejemplo: Web.Contents("https://tu-proyecto.vercel.app/api/ventas")
- Si usas `PROXY_API_KEY`, agrega el header:
```
Web.Contents("https://tu-proyecto.vercel.app/api/ventas", [Headers=[#"x-api-key"="TU_CLAVE"]])
```
