"""MCP tool: procesar_lote."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from mcp_server.config import LEADS_CSV, PROCESSED_CSV, PROJECT_ROOT
from mcp_server.core.csv_handler import (
    append_processed_row,
    filter_unprocessed,
    load_processed_keys,
    make_output_row,
    read_leads_csv,
)
from mcp_server.core.gemini_client import generar_auditoria
from mcp_server.core.lead_processor import seleccionar_variacion
from mcp_server.tools.whatsapp_link import crear_enlace_whatsapp, normalize_phone

logger = logging.getLogger(__name__)


def procesar_lote(
    csv_entrada: str | None = None,
    csv_salida: str | None = None,
    limite: int | None = None,
) -> dict:
    """
    Process a batch of leads from CSV.

    Skips already processed rows, generates audit + wa.me link, appends output.
    """
    input_path = Path(csv_entrada or LEADS_CSV)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    output_path = Path(csv_salida or PROCESSED_CSV)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    leads = read_leads_csv(input_path)
    processed_keys = load_processed_keys(output_path)
    pending = filter_unprocessed(leads, processed_keys)

    if limite is not None and limite > 0:
        pending = pending[:limite]

    stats = {
        "total_leidos": len(leads),
        "pendientes": len(pending),
        "procesados_ok": 0,
        "omitidos_fase4": 0,
        "errores_telefono": 0,
        "errores_ia": 0,
        "csv_salida": str(output_path),
    }

    for lead in pending:
        timestamp = datetime.now(timezone.utc).isoformat()
        fase = int(float(lead.get("fase_lead", 4)))
        variacion = seleccionar_variacion(fase)

        if variacion == "no_enviar":
            row = make_output_row(
                lead,
                variacion_usada="no_enviar",
                estado_procesamiento="omitido_fase4",
                timestamp_procesado=timestamp,
            )
            append_processed_row(output_path, row)
            stats["omitidos_fase4"] += 1
            continue

        telefono = str(lead.get("telefono", "")).strip()
        normalized, phone_error = normalize_phone(telefono)
        if phone_error or not normalized:
            row = make_output_row(
                lead,
                variacion_usada=variacion,
                estado_procesamiento="error_telefono",
                timestamp_procesado=timestamp,
            )
            append_processed_row(output_path, row)
            stats["errores_telefono"] += 1
            continue

        audit = generar_auditoria(
            nombre=str(lead.get("nombre", "")),
            categoria=str(lead.get("categoria", "")),
            fase_lead=fase,
            reviews=lead.get("reviews", 0),
            sitio_web=str(lead.get("sitio_web", "") or ""),
            distrito=str(lead.get("distrito", "") or ""),
        )

        if audit.get("error"):
            row = make_output_row(
                lead,
                variacion_usada=variacion,
                estado_procesamiento="error_ia",
                timestamp_procesado=timestamp,
            )
            append_processed_row(output_path, row)
            stats["errores_ia"] += 1
            continue

        mensaje = audit.get("mensaje_final", "")
        link_result = crear_enlace_whatsapp(telefono, mensaje)

        row = make_output_row(
            lead,
            variacion_usada=audit.get("variacion_usada", variacion),
            mensaje_final=mensaje,
            enlace_whatsapp=link_result.get("enlace_whatsapp", ""),
            paquete_sugerido=audit.get("paquete_sugerido", "Pro"),
            estado_procesamiento="ok" if link_result.get("valido") else "error_telefono",
            timestamp_procesado=timestamp,
        )
        append_processed_row(output_path, row)

        if link_result.get("valido"):
            stats["procesados_ok"] += 1
        else:
            stats["errores_telefono"] += 1

    return stats


def register(mcp) -> None:
    @mcp.tool(name="procesar_lote")
    def procesar_lote_tool(
        csv_entrada: str | None = None,
        csv_salida: str | None = None,
        limite: int | None = None,
    ) -> dict:
        """Procesa un lote de leads desde CSV y escribe resultados append-safe."""
        return procesar_lote(
            csv_entrada=csv_entrada,
            csv_salida=csv_salida,
            limite=limite,
        )
