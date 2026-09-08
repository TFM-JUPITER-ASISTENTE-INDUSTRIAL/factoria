import csv
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.storage.entities.alarm_definition_orm import AlarmDefinitionORM
from src.storage.entities.machine_orm import MachineORM
from src.storage.entities.plc_orm import PLCORM
from src.storage.entities.sensor_orm import SensorORM

REQUIRED_COLUMNS = {
    "alarm_id", "alarm_code", "alarm_name", "machine_id",
    "machine_name", "tag_id", "severity",
}
ALLOWED_SEVERITIES = {"ERROR", "CRITICAL_ERROR"}


def sensor_type_from_tag(tag_id: str) -> str:
    """Extrae el grupo anterior al nombre del fallo, sin una lista de tipos fija."""
    parts = tag_id.strip().split(".")
    if len(parts) < 3 or any(not part or part != part.strip() for part in parts):
        raise ValueError(f"tag_id inválido: {tag_id!r}")
    return parts[-2]


@dataclass(frozen=True)
class AlarmCatalogRow:
    alarm_id: str
    alarm_code: str
    alarm_name: str
    machine_id: str
    machine_name: str
    tag_id: str
    severity: str
    source_file: str
    source_line: int
    component: str | None = None


def load_catalog_rows(directory: Path) -> list[AlarmCatalogRow]:
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise ValueError(f"No se encontraron archivos CSV en {directory}")
    rows = []
    alarm_ids = set()
    machine_codes = set()
    names = {}
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{path.name}: faltan columnas: {sorted(missing)}")
            for line, raw in enumerate(reader, start=2):
                values = {key: (raw.get(key) or "").strip() for key in REQUIRED_COLUMNS}
                if not all(values.values()):
                    raise ValueError(f"{path.name}:{line}: campos vacíos")
                if values["severity"] not in ALLOWED_SEVERITIES:
                    raise ValueError(f"{path.name}:{line}: severity desconocida")
                sensor_type_from_tag(values["tag_id"])
                key = (values["machine_id"], values["alarm_code"])
                if values["alarm_id"] in alarm_ids:
                    raise ValueError(f"{path.name}:{line}: alarm_id duplicado")
                if key in machine_codes:
                    raise ValueError(f"{path.name}:{line}: Alarma duplicada {key}")
                previous = names.get(values["machine_id"])
                if previous is not None and previous != values["machine_name"]:
                    raise ValueError(f"{path.name}:{line}: nombres diferentes para la máquina")
                alarm_ids.add(values["alarm_id"])
                machine_codes.add(key)
                names[values["machine_id"]] = values["machine_name"]
                rows.append(AlarmCatalogRow(
                    **values, source_file=path.name, source_line=line,
                    component=(raw.get("component") or "").strip() or None,
                ))
    return rows


def get_or_create_machine(session: Session, external_id: str, name: str):
    machine = session.scalar(select(MachineORM).where(MachineORM.external_id == external_id))
    if machine is None:
        # Recupera una máquina anterior solo si su nombre coincide exactamente.
        existing = session.scalar(select(MachineORM).where(MachineORM.name == name))
        if existing is not None:
            if existing.external_id not in (None, external_id):
                raise ValueError(f"Nombre de máquina ya asociado a otro ID: {name}")
            machine = existing
            machine.external_id = external_id
    created = machine is None
    if created:
        machine = MachineORM(external_id=external_id, name=name)
        session.add(machine)
    machine.name = name
    if machine.plc is None:
        machine.plc = PLCORM(sensors=[])
    session.flush()
    return machine, created


def get_or_create_sensor(session: Session, machine: MachineORM, sensor_type: str):
    sensor = session.scalar(select(SensorORM).where(
        SensorORM.owner_id == machine.plc.id,
        SensorORM.sensor_type == sensor_type,
    ))
    created = sensor is None
    if created:
        sensor = SensorORM(
            owner=machine.plc,
            name=sensor_type,
            sensor_type=sensor_type,
            failure_probability=1.0,
            error_codes=[],
        )
        session.add(sensor)
        session.flush()
    return sensor, created


def upsert_alarm_definition(session: Session, machine: MachineORM,
                            sensor: SensorORM, row: AlarmCatalogRow) -> str:
    by_id = session.scalar(select(AlarmDefinitionORM).where(
        AlarmDefinitionORM.external_alarm_id == row.alarm_id,
    ))
    by_code = session.scalar(select(AlarmDefinitionORM).where(
        AlarmDefinitionORM.machine_id == machine.id,
        AlarmDefinitionORM.alarm_code == row.alarm_code,
    ))
    if by_id is not None and by_code is not None and by_id.id != by_code.id:
        raise ValueError(f"Conflicto entre alarm_id y código: {row.alarm_id}")
    definition = by_id if by_id is not None else by_code
    created = definition is None
    if created:
        definition = AlarmDefinitionORM(
            external_alarm_id=row.alarm_id,
            machine_id=machine.id,
            alarm_code=row.alarm_code,
        )
        session.add(definition)
    else:
        if (
            definition.external_alarm_id != row.alarm_id
            or definition.machine_id != machine.id
            or definition.alarm_code != row.alarm_code
        ):
            raise ValueError(f"Identidad de alarma incompatible: {row.alarm_id}")
        if definition.sensor_id is not None:
            old_sensor = session.get(SensorORM, definition.sensor_id)
            # Permite migrar exclusivamente la primera propuesta (sensor por tag completo).
            previous_full_tag_sensor = (
                old_sensor is not None
                and old_sensor.sensor_type is None
                and old_sensor.owner_id == machine.plc.id
                and old_sensor.tag_id == row.tag_id == definition.tag_id
            )
            if (
                definition.tag_id != row.tag_id
                or (definition.sensor_id != sensor.id and not previous_full_tag_sensor)
            ):
                raise ValueError(
                    f"{row.alarm_id}: cambiar de sensor/tag requiere una migración explícita"
                )

    values = {
        "alarm_name": row.alarm_name,
        "tag_id": row.tag_id,
        "severity": row.severity,
        "component": row.component,
        "sensor_id": sensor.id,
    }
    changed = any(getattr(definition, key) != value for key, value in values.items())
    for key, value in values.items():
        setattr(definition, key, value)
    session.flush()
    return "created" if created else ("updated" if changed else "unchanged")


def import_alarm_catalogs(session: Session, directory: Path) -> dict[str, int]:
    rows = load_catalog_rows(directory)
    result = {
        "files": len(list(directory.glob("*.csv"))), "rows": len(rows),
        "machines_created": 0, "sensors_created": 0,
        "definitions_created": 0, "definitions_updated": 0,
        "definitions_unchanged": 0,
    }
    machines = {}
    for row in rows:
        if row.machine_id not in machines:
            machine, created = get_or_create_machine(session, row.machine_id, row.machine_name)
            machines[row.machine_id] = machine
            result["machines_created"] += int(created)
        machine = machines[row.machine_id]
        sensor_type = sensor_type_from_tag(row.tag_id)
        sensor, created = get_or_create_sensor(session, machine, sensor_type)
        result["sensors_created"] += int(created)
        status = upsert_alarm_definition(session, machine, sensor, row)
        result[f"definitions_{status}"] += 1

    # error_codes se conserva como compatibilidad, derivado del catálogo.
    # El simulador usa las relaciones, no este ARRAY como fuente independiente.
    for machine in machines.values():
        for sensor in machine.plc.sensors:
            if sensor.sensor_type is not None:
                sensor.error_codes = list(session.scalars(
                    select(AlarmDefinitionORM.alarm_code)
                    .where(AlarmDefinitionORM.sensor_id == sensor.id)
                    .order_by(AlarmDefinitionORM.alarm_code)
                ))
    session.flush()

    # Completa eventos sin sensor y adapta los de la primera propuesta por tag.
    # No adivina el origen de códigos antiguos sin definición.
    linked = session.execute(text("""
        UPDATE alarms AS event
        SET sensor_id = definition.sensor_id
        FROM alarm_definitions AS definition
        WHERE event.alarm_definition_id = definition.id
          AND definition.sensor_id IS NOT NULL
          AND (
            event.sensor_id IS NULL
            OR EXISTS (
              SELECT 1 FROM sensors AS previous
              JOIN plcs ON plcs.id = previous.owner_id
              WHERE previous.id = event.sensor_id
                AND previous.sensor_type IS NULL
                AND previous.tag_id = definition.tag_id
                AND plcs.owner_id = definition.machine_id
            )
          )
          AND event.machine_id = definition.machine_id
          AND event.error_code = definition.alarm_code
          AND (
            event.status <> 'ACTIVE'
            OR NOT EXISTS (
              SELECT 1 FROM alarms AS other
              WHERE other.id <> event.id
                AND other.sensor_id = definition.sensor_id
                AND other.error_code = event.error_code
                AND other.status = 'ACTIVE'
            )
          )
    """))
    result["events_linked"] = linked.rowcount
    return result


if __name__ == "__main__":
    import argparse
    from src.storage.connectors.postgresql import SessionLocal

    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path, nargs="?", default=Path("data/alarm_catalogs"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as session:
        try:
            result = import_alarm_catalogs(session, args.directory)
            if args.dry_run:
                session.rollback()
            else:
                session.commit()
            print(result)
            print("Sin cambios guardados" if args.dry_run else "Importación completada")
        except Exception:
            session.rollback()
            raise
