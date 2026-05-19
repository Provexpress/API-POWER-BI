// lib/fetchWithToken.js
// Utilidad para obtener token y hacer peticiones autenticadas a la API externa.

const API_BASE_URL = process.env.API_BASE_URL;
const API_USERNAME = process.env.API_USERNAME;
const API_PASSWORD = process.env.API_PASSWORD;
const PROXY_API_KEY = process.env.PROXY_API_KEY;

/**
 * Valida que la peticion tenga la API key correcta.
 */
function validateApiKey(req) {
  const key = req.headers["x-api-key"];
  if (!PROXY_API_KEY) return true;
  return key === PROXY_API_KEY;
}

/**
 * Obtiene el token de autenticacion de la API externa.
 */
async function getToken() {
  const response = await fetch(`${API_BASE_URL}/api/getKey`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: API_USERNAME,
      password: API_PASSWORD,
    }),
  });

  if (!response.ok) {
    throw new Error(`Error obteniendo token: ${response.status}`);
  }

  const data = await response.json();
  return data.token;
}

/**
 * Hace una peticion autenticada a un endpoint de la API externa.
 */
async function fetchFromAPI(endpoint) {
  const token = await getToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Error consultando ${endpoint}: ${response.status}`);
  }

  return response.json();
}

module.exports = { validateApiKey, fetchFromAPI };
