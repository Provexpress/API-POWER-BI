// api/compras.js
// Endpoint: Consulta de Compras

const { validateApiKey, fetchFromAPI } = require("../lib/fetchWithToken");

module.exports = async function handler(req, res) {
  // Validar API Key
  if (!validateApiKey(req)) {
    return res.status(401).json({ error: "No autorizado" });
  }

  try {
    const data = await fetchFromAPI("/consultas/api/consultaComprasDashboardPBI");
    return res.status(200).json(data);
  } catch (error) {
    console.error("Error en compras:", error.message);
    return res.status(500).json({ error: error.message });
  }
};
