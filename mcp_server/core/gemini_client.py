"""Gemini API client with rate limiting and JSON schema."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from mcp_server.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    RATE_LIMIT_SECONDS,
    SENDER_NAME,
    SYSTEM_PROMPT_PATH,
    VARIACIONES_PATH,
)
from mcp_server.core.lead_processor import build_lead_context, variacion_instruction

logger = logging.getLogger(__name__)

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "variacion_usada": {"type": "string", "enum": ["A", "B", "C", "no_enviar"]},
        "estado_actual": {"type": "string"},
        "oportunidad_perdida": {"type": "string"},
        "solucion_ariq": {"type": "string"},
        "mensaje_final": {"type": "string"},
        "paquete_sugerido": {"type": "string", "enum": ["Basico", "Pro", "Enterprise"]},
    },
    "required": [
        "variacion_usada",
        "estado_actual",
        "oportunidad_perdida",
        "solucion_ariq",
        "mensaje_final",
        "paquete_sugerido",
    ],
}


def _load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("{TU_NOMBRE}", SENDER_NAME)


def _build_user_prompt(context: dict[str, Any]) -> str:
    variacion = context["variacion"]
    if variacion == "no_enviar":
        return (
            f"Lead: {context['nombre']} ({context['categoria']}), fase {context['fase_lead']}. "
            "No generes mensaje de outreach."
        )

    parts = [
        f"Negocio: {context['nombre']}",
        f"Categoría: {context['categoria']}",
        f"Reseñas: {context['reviews_texto']}",
        f"Distrito: {context['distrito'] or 'Arequipa'}",
        f"Fase lead: {context['fase_lead']}",
        variacion_instruction(variacion),
    ]
    if context.get("sitio_web_gancho"):
        parts.append(f"Gancho web: hoy su presencia es {context['sitio_web_gancho']}")
    elif context.get("sitio_web_raw"):
        parts.append(f"Sitio web: {context['sitio_web_raw']}")

    parts.append(
        "Genera la auditoría express y el mensaje final en JSON con las claves: "
        "variacion_usada, estado_actual, oportunidad_perdida, solucion_ariq, "
        "mensaje_final, paquete_sugerido."
    )
    return "\n".join(parts)


def generar_auditoria(
    nombre: str,
    categoria: str,
    fase_lead: int,
    reviews: int | float | str = 0,
    sitio_web: str = "",
    distrito: str = "",
) -> dict[str, Any]:
    """Call Gemini to generate audit JSON. Returns error_ia on failure."""
    context = build_lead_context(
        nombre=nombre,
        categoria=categoria,
        reviews=reviews,
        sitio_web=sitio_web,
        distrito=distrito,
        fase_lead=fase_lead,
    )

    if context["variacion"] == "no_enviar":
        return {
            "variacion_usada": "no_enviar",
            "estado_actual": "",
            "oportunidad_perdida": "",
            "solucion_ariq": "",
            "mensaje_final": "",
            "paquete_sugerido": "Pro",
            "error": None,
        }

    if not GEMINI_API_KEY:
        return _error_response("GEMINI_API_KEY no configurada")

    time.sleep(RATE_LIMIT_SECONDS)

    system_instruction = _load_prompt(SYSTEM_PROMPT_PATH)
    variaciones_ref = ""
    if VARIACIONES_PATH.exists():
        variaciones_ref = VARIACIONES_PATH.read_text(encoding="utf-8")
    if variaciones_ref:
        system_instruction = f"{system_instruction}\n\n{variaciones_ref}"

    user_prompt = _build_user_prompt(context)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
        )
        text = response.text or ""
        data = json.loads(text)
        data["error"] = None
        data["variacion_usada"] = context["variacion"]
        return data
    except Exception as exc:
        logger.exception("Error llamando a Gemini")
        return _error_response(str(exc))


def _error_response(message: str) -> dict[str, Any]:
    return {
        "variacion_usada": "no_enviar",
        "estado_actual": "",
        "oportunidad_perdida": "",
        "solucion_ariq": "",
        "mensaje_final": "",
        "paquete_sugerido": "Pro",
        "error": message,
    }
