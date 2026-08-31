"""Lead field normalization and variation selection."""

from __future__ import annotations

import math
import re
from typing import Any

SOCIAL_HOSTS = ("facebook.com", "instagram.com", "fb.com", "instagr.am")
WIX_HOSTS = ("wixsite.com", "wix.com")


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == "" or str(value).strip().lower() in ("nan", "none")


def format_reviews(reviews: Any) -> str:
    """Map empty or zero reviews to 'casi sin reseñas'."""
    if _is_empty(reviews):
        return "casi sin reseñas"
    try:
        count = int(float(reviews))
    except (TypeError, ValueError):
        return "casi sin reseñas"
    if count <= 0:
        return "casi sin reseñas"
    return f"{count} reseñas"


def format_sitio_web(sitio_web: Any) -> str | None:
    """Return web hook text or None if empty."""
    if _is_empty(sitio_web):
        return None

    url = str(sitio_web).strip().lower()
    if any(host in url for host in SOCIAL_HOSTS):
        if "instagram" in url or "instagr.am" in url:
            return "Instagram"
        return "Facebook"
    if any(host in url for host in WIX_HOSTS):
        return "Wix"
    if url.startswith("http://"):
        return "un sitio sin HTTPS"
    return None


def seleccionar_variacion(fase_lead: int, reviews: Any = 0) -> str:
    """
    Select message variation from pipeline phase.

    fase 1 → A, fase 2/3 → B, fase 4 → no_enviar.
    Variation C is reserved for future follow-up tools.
    """
    try:
        fase = int(fase_lead)
    except (TypeError, ValueError):
        return "no_enviar"

    if fase == 1:
        return "A"
    if fase in (2, 3):
        return "B"
    if fase == 4:
        return "no_enviar"
    return "no_enviar"


def build_lead_context(
    nombre: str,
    categoria: str,
    reviews: Any = 0,
    sitio_web: Any = "",
    distrito: str = "",
    fase_lead: int = 1,
) -> dict[str, Any]:
    """Normalize lead fields for Gemini prompt construction."""
    variacion = seleccionar_variacion(fase_lead, reviews)
    web_hook = format_sitio_web(sitio_web)

    context: dict[str, Any] = {
        "nombre": str(nombre).strip(),
        "categoria": str(categoria).strip(),
        "reviews_texto": format_reviews(reviews),
        "reviews_num": 0 if _is_empty(reviews) else int(float(reviews)),
        "distrito": str(distrito).strip() if not _is_empty(distrito) else "",
        "fase_lead": int(fase_lead),
        "variacion": variacion,
        "sitio_web_raw": "" if _is_empty(sitio_web) else str(sitio_web).strip(),
    }

    if web_hook:
        context["sitio_web_gancho"] = web_hook
    else:
        context["sitio_web_gancho"] = None

    return context


def variacion_instruction(variacion: str) -> str:
    """Short instruction for the selected variation."""
    instructions = {
        "A": (
            "Usa Variación A: dolor de ventas perdidas por catálogo/WhatsApp "
            "fuera de horario."
        ),
        "B": (
            "Usa Variación B: dolor de SEO local y visibilidad en Google Maps."
        ),
        "C": (
            "Usa Variación C: follow-up con beca o cupos limitados, sin cifras exactas."
        ),
    }
    return instructions.get(variacion, "No generes mensaje; marca variacion_usada como no_enviar.")
