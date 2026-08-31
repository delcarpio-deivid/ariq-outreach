"""Tests for WhatsApp link tool."""

import pytest

from mcp_server.tools.whatsapp_link import crear_enlace_whatsapp, normalize_phone


@pytest.mark.parametrize(
    "telefono,expected",
    [
        ("+51987654321", "51987654321"),
        ("987654321", "51987654321"),
        ("51987654321", "51987654321"),
        ("519 876 543 21", "51987654321"),
    ],
)
def test_normalize_phone_valid(telefono, expected):
    normalized, error = normalize_phone(telefono)
    assert error is None
    assert normalized == expected
    assert len(normalized) == 11


@pytest.mark.parametrize(
    "telefono",
    ["", "12345", "abc", None],
)
def test_normalize_phone_invalid(telefono):
    normalized, error = normalize_phone(telefono or "")
    assert normalized is None
    assert error is not None


def test_crear_enlace_whatsapp_valid():
    result = crear_enlace_whatsapp("+51987654321", "Hola mundo")
    assert result["valido"] is True
    assert result["error"] is None
    assert result["telefono_normalizado"] == "51987654321"
    assert result["enlace_whatsapp"].startswith("https://wa.me/51987654321?text=")
    assert "Hola%20mundo" in result["enlace_whatsapp"]


def test_crear_enlace_whatsapp_invalid_never_raises():
    result = crear_enlace_whatsapp("", "Hola")
    assert result["valido"] is False
    assert result["error"] is not None
