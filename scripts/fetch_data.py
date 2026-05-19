#!/usr/bin/env python3
"""
Proveexpress - ETL diario para Power BI.
Descarga datos de la API externa y los guarda como CSV.
"""

from __future__ import annotations

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


ENDPOINTS = {
    "ventas": "/consultas/api/consultaVentasDashboardPBI",
    "compras": "/consultas/api/consultaComprasDashboardPBI",
    "estados_entregas": "/consultas/api/consultaEstadosEntregasDocumentosDashboardPBI",
    "cotizaciones_estados": "/consultas/api/consultaCotizacionesEstadosDashboardPBI",
    "clientes_sectores": "/consultas/api/consultaClientesSectoresDashboardPBI",
    "empleados": "/consultas/api/consultaPersonalPBI",
}


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value


def get_settings() -> tuple[str, str, str, Path]:
    api_base = required_env("API_BASE_URL").rstrip("/")
    api_user = required_env("API_USERNAME")
    api_pass = required_env("API_PASSWORD")
    output_dir = Path(os.environ.get("OUTPUT_DIR", "data"))
    return api_base, api_user, api_pass, output_dir


def get_token(session: requests.Session, api_base: str, api_user: str, api_pass: str) -> str:
    """
    Obtiene token de autenticacion de la API externa.
    El Power Query original tomaba el segundo campo del objeto si no habia un
    nombre de campo estandar para el token.
    """
    print("  Llamando a /api/getKey...")
    response = session.post(
        f"{api_base}/api/getKey",
        json={"username": api_user, "password": api_pass},
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict) or not data:
        raise RuntimeError("La respuesta de autenticacion no es un objeto JSON valido.")

    for field in ("token", "Token", "access_token", "accessToken", "key"):
        if data.get(field):
            return str(data[field])

    keys = list(data.keys())
    if len(keys) >= 2:
        value = data[keys[1]]
        if isinstance(value, dict):
            for field in ("token", "Token", "key"):
                if value.get(field):
                    return str(value[field])
        if value:
            return str(value)

    first_value = data[keys[0]]
    if first_value:
        return str(first_value)

    raise RuntimeError("No se encontro token en la respuesta de autenticacion.")


def fetch_endpoint(session: requests.Session, api_base: str, token: str, path: str) -> Any:
    """Consulta un endpoint con autenticacion Bearer."""
    print(f"  GET {api_base}{path}")
    response = session.get(
        f"{api_base}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and "response" in data:
        return data["response"]
    return data


def normalize_records(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, dict):
        for field in ("data", "items", "results", "records", "response"):
            value = payload.get(field)
            if isinstance(value, list):
                payload = value
                break

    if not isinstance(payload, list):
        raise RuntimeError(f"Se esperaba una lista de registros y llego {type(payload).__name__}.")

    records: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise RuntimeError("La API devolvio elementos que no son objetos JSON.")
        records.append(item)

    return records


def fieldnames_for(records: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    seen: set[str] = set()

    for record in records:
        for key in record:
            if not key or not str(key).strip():
                continue
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    return fieldnames


def save_csv(records: list[dict[str, Any]], filepath: Path) -> int:
    """Guarda una lista de registros como CSV UTF-8 con BOM para Excel/PBI."""
    if not records:
        print(f"  [!] Sin registros para {filepath}")
        return 0

    fieldnames = fieldnames_for(records)
    if not fieldnames:
        raise RuntimeError(f"No hay columnas validas para {filepath}")

    with filepath.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"  -> {filepath} | {len(records):,} registros | {size_mb:.1f} MB")
    return len(records)


def main() -> int:
    try:
        api_base, api_user, api_pass, output_dir = get_settings()
    except RuntimeError as exc:
        print(f"ERROR configurando ETL: {exc}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  Proveexpress ETL - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    with requests.Session() as session:
        print("\n[1/2] Obteniendo token...")
        try:
            token = get_token(session, api_base, api_user, api_pass)
            print("  Token obtenido correctamente")
        except Exception as exc:
            print(f"  ERROR obteniendo token: {exc}")
            return 1

        print("\n[2/2] Descargando datos...\n")
        total = 0
        for name, path in ENDPOINTS.items():
            print(f"--- {name.upper()} ---")
            try:
                payload = fetch_endpoint(session, api_base, token, path)
                records = normalize_records(payload)
                total += save_csv(records, output_dir / f"{name}.csv")
            except Exception as exc:
                print(f"  ERROR en {name}: {exc}")
                return 1
            print()

    print("=" * 60)
    print(f"  COMPLETADO | {total:,} registros totales")
    print(f"  Archivos en: ./{output_dir}/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
