import csv
from pathlib import Path

import pytest

from src.storage.importers.alarm_catalog_importer import load_catalog_rows


REQUIRED_COLUMNS = [
    "alarm_id",
    "alarm_code",
    "alarm_name",
    "machine_id",
    "machine_name",
    "tag_id",
    "severity",
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def valid_row(**changes: str) -> dict[str, str]:
    row = {
        "alarm_id": "ALM-TEST-0001",
        "alarm_code": "TEST-0001",
        "alarm_name": "Test alarm",
        "machine_id": "TEST-01",
        "machine_name": "Test machine",
        "tag_id": "TEST.MACHINE.ALARM_1",
        "severity": "ERROR",
    }
    row.update(changes)
    return row


def test_real_catalogs_have_expected_size_and_machine_count():
    rows = load_catalog_rows(Path("data/alarm_catalogs"))

    assert len(rows) == 165
    assert len({row.machine_id for row in rows}) == 5


def test_importer_rejects_missing_required_column(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text(
        "alarm_id,alarm_code\nALM-1,CODE-1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="faltan columnas"):
        load_catalog_rows(tmp_path)


def test_importer_rejects_duplicate_machine_code(tmp_path):
    path = tmp_path / "duplicates.csv"
    write_csv(
        path,
        [
            valid_row(),
            valid_row(
                alarm_id="ALM-TEST-0002",
                tag_id="TEST.MACHINE.ALARM_2",
            ),
        ],
    )

    with pytest.raises(ValueError, match="Alarma duplicada"):
        load_catalog_rows(tmp_path)


def test_importer_rejects_unknown_severity(tmp_path):
    path = tmp_path / "invalid_severity.csv"
    write_csv(path, [valid_row(severity="UNKNOWN")])

    with pytest.raises(ValueError, match="severity desconocida"):
        load_catalog_rows(tmp_path)
