#!/usr/bin/env python3
"""
Sube archivos CSV a SharePoint via Microsoft Graph API.
Requiere una App Registration con permisos de escritura sobre el sitio.
"""

from __future__ import annotations

import os
import sys
import base64
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests


GRAPH_BASE = "https://graph.microsoft.com/v1.0"
CHUNK_SIZE = 10 * 1024 * 1024


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value


def get_graph_token(session: requests.Session) -> str:
    """Obtiene token de Microsoft Graph API."""
    tenant_id = required_env("AZURE_TENANT_ID")
    client_id = required_env("AZURE_CLIENT_ID")
    client_secret = required_env("AZURE_CLIENT_SECRET")

    response = session.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def graph_request(
    session: requests.Session,
    method: str,
    url: str,
    token: str,
    **kwargs: Any,
) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    return session.request(method, url, headers=headers, timeout=120, **kwargs)


def share_url_to_id(folder_url: str) -> str:
    encoded = base64.urlsafe_b64encode(folder_url.encode("utf-8")).decode("ascii")
    return f"u!{encoded.rstrip('=')}"


def resolve_shared_folder(
    session: requests.Session,
    token: str,
    folder_url: str,
) -> tuple[str, str]:
    share_id = share_url_to_id(folder_url)
    response = graph_request(session, "GET", f"{GRAPH_BASE}/shares/{share_id}/driveItem", token)
    response.raise_for_status()
    item = response.json()

    if "folder" not in item:
        raise RuntimeError("SHAREPOINT_FOLDER_URL debe apuntar a una carpeta, no a un archivo.")

    parent_reference = item.get("parentReference", {})
    drive_id = parent_reference.get("driveId")
    item_id = item.get("id")
    if not drive_id or not item_id:
        raise RuntimeError("No se pudo resolver driveId/itemId desde SHAREPOINT_FOLDER_URL.")

    return drive_id, item_id


def parse_site_url(site_url: str) -> tuple[str, str]:
    parsed = urlparse(site_url)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError("SHAREPOINT_SITE_URL debe ser una URL completa de SharePoint.")
    return parsed.netloc, parsed.path.strip("/")


def get_site_by_url(session: requests.Session, token: str, site_url: str) -> dict[str, Any]:
    hostname, site_path = parse_site_url(site_url)
    if site_path:
        encoded_path = quote(site_path, safe="/")
        url = f"{GRAPH_BASE}/sites/{hostname}:/{encoded_path}"
    else:
        url = f"{GRAPH_BASE}/sites/{hostname}"

    response = graph_request(session, "GET", url, token)
    response.raise_for_status()
    return response.json()


def get_site_by_search(session: requests.Session, token: str, search_term: str) -> dict[str, Any]:
    response = graph_request(
        session,
        "GET",
        f"{GRAPH_BASE}/sites?search={quote(search_term)}",
        token,
    )
    response.raise_for_status()
    sites = response.json().get("value", [])
    if not sites:
        raise RuntimeError(f"No se encontro el sitio de SharePoint '{search_term}'.")
    return sites[0]


def resolve_site_id(session: requests.Session, token: str) -> str:
    site_id = os.environ.get("SHAREPOINT_SITE_ID", "").strip()
    if site_id:
        return site_id

    site_url = os.environ.get("SHAREPOINT_SITE_URL", "").strip()
    if site_url:
        return get_site_by_url(session, token, site_url)["id"]

    site_ref = os.environ.get("SHAREPOINT_SITE", "").strip()
    if not site_ref:
        raise RuntimeError("Configura SHAREPOINT_SITE_URL, SHAREPOINT_SITE_ID o SHAREPOINT_SITE.")

    if site_ref.startswith("https://"):
        return get_site_by_url(session, token, site_ref)["id"]

    if ".sharepoint.com" in site_ref and " " not in site_ref:
        site_url = f"https://{site_ref}"
        return get_site_by_url(session, token, site_url)["id"]

    return get_site_by_search(session, token, site_ref)["id"]


def resolve_drive_id(session: requests.Session, token: str, site_id: str | None = None) -> str:
    drive_id = os.environ.get("SHAREPOINT_DRIVE_ID", "").strip()
    if drive_id:
        return drive_id

    if not site_id:
        raise RuntimeError("Configura SHAREPOINT_DRIVE_ID o un sitio de SharePoint valido.")

    response = graph_request(session, "GET", f"{GRAPH_BASE}/sites/{site_id}/drive", token)
    response.raise_for_status()
    return response.json()["id"]


def graph_path(path: str) -> str:
    return quote(path.strip("/"), safe="/")


def get_drive_root_id(session: requests.Session, token: str, drive_id: str) -> str:
    response = graph_request(session, "GET", f"{GRAPH_BASE}/drives/{drive_id}/root", token)
    response.raise_for_status()
    return response.json()["id"]


def find_child_folder(
    session: requests.Session,
    token: str,
    drive_id: str,
    parent_id: str,
    folder_name: str,
) -> str | None:
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{parent_id}/children"

    while url:
        response = graph_request(session, "GET", url, token)
        response.raise_for_status()
        payload = response.json()
        for child in payload.get("value", []):
            if child.get("name") == folder_name and "folder" in child:
                return child["id"]
        url = payload.get("@odata.nextLink")

    return None


def create_child_folder(
    session: requests.Session,
    token: str,
    drive_id: str,
    parent_id: str,
    folder_name: str,
) -> str:
    response = graph_request(
        session,
        "POST",
        f"{GRAPH_BASE}/drives/{drive_id}/items/{parent_id}/children",
        token,
        json={
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )

    if response.status_code == 409:
        existing_id = find_child_folder(session, token, drive_id, parent_id, folder_name)
        if existing_id:
            return existing_id

    response.raise_for_status()
    return response.json()["id"]


def ensure_folder_path(
    session: requests.Session,
    token: str,
    drive_id: str,
    parent_id: str,
    folder_path: str,
) -> str:
    parts = [part for part in folder_path.strip("/").split("/") if part]
    current_id = parent_id

    for part in parts:
        child_id = find_child_folder(session, token, drive_id, current_id, part)
        if not child_id:
            child_id = create_child_folder(session, token, drive_id, current_id, part)
        current_id = child_id

    return current_id


def upload_file(
    session: requests.Session,
    token: str,
    drive_id: str,
    folder_id: str,
    local_path: Path,
) -> None:
    file_size = local_path.stat().st_size
    remote_filename = quote(local_path.name, safe="")

    if file_size < 4 * 1024 * 1024:
        url = f"{GRAPH_BASE}/drives/{drive_id}/items/{folder_id}:/{remote_filename}:/content"
        with local_path.open("rb") as file:
            response = graph_request(
                session,
                "PUT",
                url,
                token,
                headers={"Content-Type": "application/octet-stream"},
                data=file,
            )
        response.raise_for_status()
    else:
        url = f"{GRAPH_BASE}/drives/{drive_id}/items/{folder_id}:/{remote_filename}:/createUploadSession"
        session_response = graph_request(
            session,
            "POST",
            url,
            token,
            json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
        )
        session_response.raise_for_status()
        upload_url = session_response.json()["uploadUrl"]

        with local_path.open("rb") as file:
            start = 0
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    break
                end = start + len(chunk) - 1
                response = session.put(
                    upload_url,
                    headers={
                        "Content-Range": f"bytes {start}-{end}/{file_size}",
                        "Content-Length": str(len(chunk)),
                    },
                    data=chunk,
                    timeout=600,
                )
                if response.status_code not in (200, 201, 202):
                    raise RuntimeError(f"Error subiendo chunk: {response.status_code} {response.text}")
                start = end + 1

    print(f"  -> Subido: {local_path.name} ({file_size / (1024 * 1024):.1f} MB)")


def csv_files(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        raise RuntimeError(f"No existe el directorio de datos: {data_dir}")

    files = sorted(path for path in data_dir.iterdir() if path.suffix.lower() == ".csv")
    if not files:
        raise RuntimeError(f"No se encontraron archivos CSV en {data_dir}")
    return files


def main() -> int:
    data_dir = Path(os.environ.get("OUTPUT_DIR", "data"))
    folder_url = os.environ.get("SHAREPOINT_FOLDER_URL", "").strip()
    folder_path = os.environ.get("SHAREPOINT_FOLDER", "").strip("/")
    if folder_url:
        folder_path = ""
    elif not folder_path:
        folder_path = "PowerBI/Proveexpress"

    try:
        files = csv_files(data_dir)
        with requests.Session() as session:
            print("Obteniendo token de Graph API...")
            token = get_graph_token(session)

            if folder_url:
                print("Resolviendo carpeta destino desde SHAREPOINT_FOLDER_URL...")
                drive_id, base_folder_id = resolve_shared_folder(session, token, folder_url)
            elif os.environ.get("SHAREPOINT_DRIVE_ID", "").strip():
                print("Resolviendo drive de SharePoint...")
                drive_id = resolve_drive_id(session, token)
                base_folder_id = get_drive_root_id(session, token, drive_id)
            else:
                print("Resolviendo sitio y drive de SharePoint...")
                site_id = resolve_site_id(session, token)
                drive_id = resolve_drive_id(session, token, site_id)
                base_folder_id = get_drive_root_id(session, token, drive_id)

            if folder_path:
                print(f"Verificando carpeta destino: {folder_path}/...")
                target_folder_id = ensure_folder_path(session, token, drive_id, base_folder_id, folder_path)
            else:
                print("Usando la carpeta compartida como destino.")
                target_folder_id = base_folder_id

            print("Subiendo archivos a SharePoint...\n")
            for local_path in files:
                upload_file(session, token, drive_id, target_folder_id, local_path)
    except Exception as exc:
        print(f"ERROR subiendo a SharePoint: {exc}")
        return 1

    print("\nSubida completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
