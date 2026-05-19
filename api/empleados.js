// api/empleados.js
// Endpoint: Personal / Empleados

const { validateApiKey, fetchFromAPI } = require("../lib/fetchWithToken");

module.exports = async function handler(req, res) {
  // Validar API Key
  if (!validateApiKey(req)) {
    return res.status(401).json({ error: "No autorizado" });
  }

  try {
    const data = await fetchFromAPI("/consultas/api/consultaPersonalPBI");
    return res.status(200).json(data);
  } catch (error) {
    console.error("Error en empleados:", error.message);
    return res.status(500).json({ error: error.message });
  }
};
