"""MCP tool: crear_enlace_whatsapp."""

from __future__ import annotations

import re
from urllib.parse import quote

from pydantic import BaseModel, Field

from mcp_server.config import COUNTRY_CODE


class WhatsAppInput(BaseModel):
    telefono: str = Field(description="Número de teléfono del lead")
    mensaje: str = Field(max_length=1000, description="Texto del mensaje redactado")


class WhatsAppOutput(BaseModel):
    telefono_normalizado: str
    enlace_whatsapp: str
    valido: bool
    error: str | None = None


def normalize_phone(telefono: str, country_code: str = COUNTRY_CODE) -> tuple[str | None, str | None]:
    """Normalize Peruvian phone to 51XXXXXXXXX (11 digits)."""
    if telefono is None or str(telefono).strip() == "":
        return None, "Teléfono vacío"

    digits = re.sub(r"\D", "", str(telefono))
    cc = re.sub(r"\D", "", country_code) or "51"

    if len(digits) == 9:
        digits = f"{cc}{digits}"
    elif len(digits) == 11 and digits.startswith(cc):
        pass
    elif len(digits) > 11 and digits.startswith(cc):
        digits = digits[:11]
    elif len(digits) == 10 and digits.startswith("0"):
        digits = f"{cc}{digits[1:]}"
    else:
        return None, f"Formato de teléfono inválido: {telefono}"

    if len(digits) != 11 or not digits.startswith(cc):
        return None, f"Se esperaban 11 dígitos con prefijo {cc}, recibido: {len(digits)}"

    return digits, None


def crear_enlace_whatsapp(telefono: str, mensaje: str) -> dict:
    """Build wa.me link. Never raises; returns valido=false on error."""
    try:
        normalized, error = normalize_phone(telefono)
        if error or not normalized:
            return WhatsAppOutput(
                telefono_normalizado="",
                enlace_whatsapp="",
                valido=False,
                error=error or "Teléfono inválido",
            ).model_dump()

        encoded = quote(mensaje or "", safe="")
        link = f"https://wa.me/{normalized}?text={encoded}"
        return WhatsAppOutput(
            telefono_normalizado=normalized,
            enlace_whatsapp=link,
            valido=True,
            error=None,
        ).model_dump()
    except Exception as exc:
        return WhatsAppOutput(
            telefono_normalizado="",
            enlace_whatsapp="",
            valido=False,
            error=str(exc),
        ).model_dump()


def register(mcp) -> None:
    @mcp.tool(name="crear_enlace_whatsapp")
    def crear_enlace_whatsapp_tool(telefono: str, mensaje: str) -> dict:
        """Normaliza teléfono peruano y construye deep link wa.me."""
        return crear_enlace_whatsapp(telefono=telefono, mensaje=mensaje)
