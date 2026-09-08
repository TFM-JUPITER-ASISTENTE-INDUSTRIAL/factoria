import csv
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.entities.alarm_definition_orm import (
    AlarmDefinitionORM,
)
from src.storage.entities.machine_orm import MachineORM
from src.storage.entities.plc_orm import PLCORM
from src.storage.entities.sensor_orm import SensorORM


REQUIRED_COLUMNS = {
    "alarm_id",
    "alarm_code",
    "alarm_name",
    "machine_id",
    "machine_name",
    "tag_id",
    "severity",
}

# Debes ampliar esta lista después de revisar todos los CSV.
ALLOWED_SEVERITIES = {
    "ERROR",
    "CRITICAL_ERROR",
}


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


#esta función carga y valida los archivos CSV de catálogo de alarmas, asegurando que no haya duplicados ni inconsistencias en los datos.
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





#esta función obtiene o crea una máquina en la base de datos según el external_id y el nombre proporcionados. Si la máquina no existe, se crea una nueva entrada; si existe pero el nombre es diferente, se actualiza el nombre.
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


def get_or_create_sensor(session: Session, machine: MachineORM, tag_id: str):
    sensor = session.scalar(select(SensorORM).where(
        SensorORM.owner_id == machine.plc.id,
        SensorORM.tag_id == tag_id,
    ))
    created = sensor is None
    if created:
        sensor = SensorORM(
            owner=machine.plc,
            name=tag_id,
            tag_id=tag_id,
            failure_probability=1.0,
            error_codes=[],
        )
        session.add(sensor)
        session.flush()
    return sensor, created


#esta función inserta o actualiza una definición de alarma en la base de datos. Verifica si la definición ya existe por external_alarm_id o por la combinación de machine_id y alarm_code. Si existe, actualiza los campos si es necesario; si no, crea una nueva entrada. También maneja conflictos y asegura que no se cambien las relaciones existentes.
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
        if definition.sensor_id is not None and (
            definition.sensor_id != sensor.id or definition.tag_id != row.tag_id
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




#esta función importa los catálogos de alarmas desde los archivos CSV en el directorio especificado. Valida los datos, crea o actualiza máquinas y definiciones de alarmas según sea necesario, y devuelve un resumen de la operación.
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
        sensor, created = get_or_create_sensor(session, machine, row.tag_id)
        result["sensors_created"] += int(created)
        status = upsert_alarm_definition(session, machine, sensor, row)
        result[f"definitions_{status}"] += 1

    # error_codes se conserva como compatibilidad, derivado del catálogo.
    # El simulador usa las relaciones, no este ARRAY como fuente independiente.
    for machine in machines.values():
        for sensor in machine.plc.sensors:
            if sensor.tag_id is not None:
                sensor.error_codes = list(session.scalars(
                    select(AlarmDefinitionORM.alarm_code)
                    .where(AlarmDefinitionORM.sensor_id == sensor.id)
                    .order_by(AlarmDefinitionORM.alarm_code)
                ))
    session.flush()

    # Solo completar enlaces inequívocos de eventos YA vinculados a una definición.
    # No tocar sensores existentes ni adivinar el origen de códigos antiguos.
    linked = session.execute(text("""
        UPDATE alarms AS event
        SET sensor_id = definition.sensor_id
        FROM alarm_definitions AS definition
        WHERE event.alarm_definition_id = definition.id
          AND event.sensor_id IS NULL
          AND definition.sensor_id IS NOT NULL
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



#esta función importa los catálogos de alarmas desde los archivos CSV en el directorio especificado. Valida los datos, crea o actualiza máquinas y definiciones de alarmas según sea necesario, y devuelve un resumen de la operación.
def import_alarm_catalogs(
    session: Session,
    directory: Path,
) -> dict[str, int]:
    # Primero se leen y validan todos los archivos.
    rows = load_catalog_rows(directory)

    machines: dict[str, MachineORM] = {}

    result = {
        "files": len(list(directory.glob("*.csv"))),
        "rows": len(rows),
        "machines_created": 0,
        "definitions_created": 0,
        "definitions_updated": 0,
        "definitions_unchanged": 0,
    }

    for row in rows:
        machine = machines.get(row.machine_id)

        if machine is None:
            machine, created = get_or_create_machine(
                session=session,
                external_id=row.machine_id,
                name=row.machine_name,
            )

            machines[row.machine_id] = machine

            if created:
                result["machines_created"] += 1

        status = upsert_alarm_definition(
            session=session,
            machine=machine,
            row=row,
        )

        result[f"definitions_{status}"] += 1

    return result



#este bloque de código permite ejecutar el script directamente desde la línea de comandos, proporcionando un directorio de archivos CSV y una opción de "dry-run" 
# para validar los datos sin realizar cambios en la base de datos. Se encarga de manejar la sesión de la base de datos y mostrar un resumen del resultado de la importación.
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