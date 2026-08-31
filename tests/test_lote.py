"""Tests for batch processing with mocked Gemini."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from mcp_server.tools.lote import procesar_lote

FIXTURES = Path(__file__).parent / "fixtures" / "leads_sample.csv"


@patch("mcp_server.tools.lote.generar_auditoria")
def test_procesar_lote_fixture_mocked(mock_generar, tmp_path):
    mock_generar.return_value = {
        "variacion_usada": "A",
        "estado_actual": "Sin web",
        "oportunidad_perdida": "Ventas fuera de horario",
        "solucion_ariq": "Bot WhatsApp",
        "mensaje_final": "Hola, soy consultor de ARIQ Labs. ¿Te interesa?",
        "paquete_sugerido": "Pro",
        "error": None,
    }

    output = tmp_path / "processed.csv"
    stats = procesar_lote(
        csv_entrada=str(FIXTURES),
        csv_salida=str(output),
        limite=2,
    )

    assert stats["pendientes"] == 2
    assert output.exists()
    df = pd.read_csv(output)
    assert len(df) == 2
    assert mock_generar.call_count == 2


@patch("mcp_server.tools.lote.generar_auditoria")
def test_procesar_lote_skips_fase4(mock_generar, tmp_path):
    output = tmp_path / "processed.csv"
    input_csv = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {
                "nombre": "Consolidado",
                "telefono": "+51911111111",
                "sitio_web": "",
                "direccion": "",
                "rating": 4.0,
                "reviews": 10,
                "place_id": "ChIJphase4",
                "categoria": "boutique",
                "distrito": "Sachaca",
                "archivo_origen": "fixture.csv",
                "nombre_normalizado": "consolidado",
                "direccion_incompleta": False,
                "revisar_manualmente": False,
                "fase_lead": 4,
                "prioridad_score": 4,
            }
        ]
    ).to_csv(input_csv, index=False)

    stats = procesar_lote(csv_entrada=str(input_csv), csv_salida=str(output))
    assert stats["omitidos_fase4"] == 1
    assert mock_generar.call_count == 0
