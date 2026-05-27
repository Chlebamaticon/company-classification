import json
from pathlib import Path

from salespatriot_shared.fsc import FSCCatalog


def test_load_and_lookup(tmp_path: Path):
    catalog_path = tmp_path / "fsc.json"
    catalog_path.write_text(
        json.dumps(
            [
                {"code": "3408", "title": "Machining Centers and Way-Type Machine"},
                {"code": "1620", "title": "Aircraft Landing Gear Components"},
            ]
        ),
        encoding="utf-8",
    )
    catalog = FSCCatalog.load(catalog_path)
    assert len(catalog) == 2
    assert "3408" in catalog
    assert catalog.lookup("3408").title.startswith("Machining")
    assert catalog.lookup("9999") is None


def test_real_catalog_loads_if_present():
    """If data/fsc_catalog.json has been generated, smoke check it."""
    repo_root = Path(__file__).resolve().parents[3]
    catalog_file = repo_root / "data" / "fsc_catalog.json"
    if not catalog_file.exists():
        return
    catalog = FSCCatalog.load(catalog_file)
    assert len(catalog) > 100
    for entry in catalog.list_all():
        assert len(entry.code) == 4 and entry.code.isdigit()
        assert entry.title.strip()
