"""Tests for csv_handler deduplication."""

from pathlib import Path

import pandas as pd

from mcp_server.core.csv_handler import (
    filter_unprocessed,
    load_processed_keys,
    read_leads_csv,
)


FIXTURES = Path(__file__).parent / "fixtures" / "leads_sample.csv"


def test_read_leads_fixture():
    leads = read_leads_csv(FIXTURES)
    assert len(leads) == 5
    assert "nombre" in leads[0]
    assert "fase_lead" in leads[0]


def test_dedup_by_place_id():
    leads = read_leads_csv(FIXTURES)
    processed = {
        "place_id:ChIJfake0000000000000000001",
    }
    pending = filter_unprocessed(leads, processed)
    assert len(pending) == 4
    assert all(
        lead.get("place_id") != "ChIJfake0000000000000000001" for lead in pending
    )


def test_dedup_by_nombre_telefono_when_no_place_id(tmp_path):
    leads = [
        {"nombre": "Sin ID", "telefono": "+51922222222", "place_id": ""},
        {"nombre": "Otro", "telefono": "+51933333333", "place_id": ""},
    ]
    processed = {"nombre_tel:sin id|+51922222222"}
    pending = filter_unprocessed(leads, processed)
    assert len(pending) == 1
    assert pending[0]["nombre"] == "Otro"


def test_load_processed_keys_from_file(tmp_path):
    csv_path = tmp_path / "processed.csv"
    df = pd.DataFrame(
        [
            {
                "nombre": "Demo",
                "telefono": "+51987654321",
                "place_id": "ChIJfake0000000000000000001",
            }
        ]
    )
    df.to_csv(csv_path, index=False)
    keys = load_processed_keys(csv_path)
    assert "place_id:ChIJfake0000000000000000001" in keys
