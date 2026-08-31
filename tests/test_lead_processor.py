"""Tests for lead_processor."""

import pytest

from mcp_server.core.lead_processor import (
    build_lead_context,
    format_reviews,
    format_sitio_web,
    seleccionar_variacion,
)


@pytest.mark.parametrize(
    "reviews,expected",
    [
        (0, "casi sin reseñas"),
        ("0", "casi sin reseñas"),
        (None, "casi sin reseñas"),
        ("", "casi sin reseñas"),
        (float("nan"), "casi sin reseñas"),
        (12, "12 reseñas"),
        ("5", "5 reseñas"),
    ],
)
def test_format_reviews(reviews, expected):
    assert format_reviews(reviews) == expected


@pytest.mark.parametrize(
    "sitio,expected",
    [
        ("", None),
        (None, None),
        ("https://facebook.com/tienda", "Facebook"),
        ("https://www.instagram.com/tienda", "Instagram"),
        ("https://mitienda.wixsite.com/demo", "Wix"),
        ("http://ejemplo.com", "un sitio sin HTTPS"),
        ("https://mitienda.com", None),
    ],
)
def test_format_sitio_web(sitio, expected):
    assert format_sitio_web(sitio) == expected


@pytest.mark.parametrize(
    "fase,expected",
    [
        (1, "A"),
        (2, "B"),
        (3, "B"),
        (4, "no_enviar"),
        (99, "no_enviar"),
    ],
)
def test_seleccionar_variacion(fase, expected):
    assert seleccionar_variacion(fase) == expected


def test_build_lead_context_omits_empty_sitio():
    ctx = build_lead_context("Demo", "ferreteria", reviews=0, sitio_web="", fase_lead=1)
    assert ctx["sitio_web_gancho"] is None
    assert ctx["variacion"] == "A"


def test_build_lead_context_social_hook():
    ctx = build_lead_context(
        "Demo",
        "boutique",
        reviews=3,
        sitio_web="https://facebook.com/demo",
        fase_lead=2,
    )
    assert ctx["sitio_web_gancho"] == "Facebook"
    assert ctx["variacion"] == "B"
