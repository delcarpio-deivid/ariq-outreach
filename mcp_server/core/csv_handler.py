"""CSV read/write with append-safe deduplication."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"nombre", "categoria", "telefono", "fase_lead"}
OPTIONAL_COLUMNS = {
    "place_id",
    "sitio_web",
    "reviews",
    "rating",
    "distrito",
    "direccion",
    "archivo_origen",
    "nombre_normalizado",
    "direccion_incompleta",
    "revisar_manualmente",
    "prioridad_score",
}

OUTPUT_COLUMNS = [
    "variacion_usada",
    "mensaje_final",
    "enlace_whatsapp",
    "paquete_sugerido",
    "estado_procesamiento",
    "timestamp_procesado",
]


def _lead_key(row: dict[str, Any]) -> str:
    place_id = row.get("place_id")
    if place_id is not None and str(place_id).strip() not in ("", "nan", "None"):
        return f"place_id:{str(place_id).strip()}"
    nombre = str(row.get("nombre", "")).strip().lower()
    telefono = str(row.get("telefono", "")).strip()
    return f"nombre_tel:{nombre}|{telefono}"


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            normalized[key] = ""
        elif isinstance(value, float) and value.is_integer():
            normalized[key] = int(value)
        else:
            normalized[key] = value
    return normalized


def validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Columnas obligatorias faltantes: {sorted(missing)}")


def read_leads_csv(path: str | Path) -> list[dict[str, Any]]:
    """Read leads CSV, validating schema and skipping corrupt rows."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    validate_columns(df)

    leads: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        try:
            lead = _normalize_row(row.to_dict())
            if not str(lead.get("nombre", "")).strip():
                logger.warning("Fila %s omitida: nombre vacío", idx)
                continue
            leads.append(lead)
        except Exception as exc:
            logger.warning("Fila %s omitida por error: %s", idx, exc)
            continue

    return leads


def load_processed_keys(path: str | Path) -> set[str]:
    """Load deduplication keys from processed CSV."""
    csv_path = Path(path)
    if not csv_path.exists():
        return set()

    try:
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    except Exception as exc:
        logger.warning("No se pudo leer processed CSV: %s", exc)
        return set()

    keys: set[str] = set()
    for _, row in df.iterrows():
        keys.add(_lead_key(_normalize_row(row.to_dict())))
    return keys


def append_processed_row(path: str | Path, row: dict[str, Any]) -> None:
    """Append one processed row, creating file with headers if needed."""
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    df_new = pd.DataFrame([row])
    if csv_path.exists():
        df_new.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        df_new.to_csv(csv_path, mode="w", header=True, index=False)


def filter_unprocessed(
    leads: list[dict[str, Any]], processed_keys: set[str]
) -> list[dict[str, Any]]:
    """Return leads not yet present in processed output."""
    return [lead for lead in leads if _lead_key(lead) not in processed_keys]


def make_output_row(
    lead: dict[str, Any],
    *,
    variacion_usada: str = "",
    mensaje_final: str = "",
    enlace_whatsapp: str = "",
    paquete_sugerido: str = "",
    estado_procesamiento: str = "ok",
    timestamp_procesado: str = "",
) -> dict[str, Any]:
    """Merge input lead with output columns."""
    output = dict(lead)
    output.update(
        {
            "variacion_usada": variacion_usada,
            "mensaje_final": mensaje_final,
            "enlace_whatsapp": enlace_whatsapp,
            "paquete_sugerido": paquete_sugerido,
            "estado_procesamiento": estado_procesamiento,
            "timestamp_procesado": timestamp_procesado,
        }
    )
    return output
