"""MCP tool: generar_auditoria_express."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mcp_server.core.gemini_client import generar_auditoria


class AuditoriaInput(BaseModel):
    nombre: str = Field(description="Nombre comercial del negocio")
    categoria: str = Field(description="Rubro del negocio")
    fase_lead: Literal[1, 2, 3, 4] = Field(description="Fase del pipeline")
    reviews: int = Field(default=0, ge=0, description="Número de reseñas en Google Maps")
    sitio_web: str = Field(default="", description="URL o red social del negocio")
    distrito: str = Field(default="", description="Distrito de Arequipa")


class AuditoriaOutput(BaseModel):
    variacion_usada: Literal["A", "B", "C", "no_enviar"]
    estado_actual: str
    oportunidad_perdida: str
    solucion_ariq: str
    mensaje_final: str
    paquete_sugerido: Literal["Basico", "Pro", "Enterprise"]
    error: str | None = None


def generar_auditoria_express(
    nombre: str,
    categoria: str,
    fase_lead: int,
    reviews: int = 0,
    sitio_web: str = "",
    distrito: str = "",
) -> dict:
    """Generate digital express audit for a single lead."""
    result = generar_auditoria(
        nombre=nombre,
        categoria=categoria,
        fase_lead=fase_lead,
        reviews=reviews,
        sitio_web=sitio_web,
        distrito=distrito,
    )
    return AuditoriaOutput(**result).model_dump()


def register(mcp) -> None:
    @mcp.tool(name="generar_auditoria_express")
    def generar_auditoria_express_tool(
        nombre: str,
        categoria: str,
        fase_lead: int,
        reviews: int = 0,
        sitio_web: str = "",
        distrito: str = "",
    ) -> dict:
        """Genera una Auditoría Express Digital personalizada para un lead."""
        return generar_auditoria_express(
            nombre=nombre,
            categoria=categoria,
            fase_lead=fase_lead,
            reviews=reviews,
            sitio_web=sitio_web,
            distrito=distrito,
        )
