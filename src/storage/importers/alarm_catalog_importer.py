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


#esta función carga y valida los archivos CSV de catálogo de alarmas, asegurando que no haya duplicados ni inconsistencias en los datos.
def load_catalog_rows(
    directory: Path,
) -> list[AlarmCatalogRow]:
    csv_files = sorted(directory.glob("*.csv"))

    if not csv_files:
        raise ValueError(
            f"No se encontraron archivos CSV en {directory}"
        )

    rows: list[AlarmCatalogRow] = []

    seen_alarm_ids: dict[str, AlarmCatalogRow] = {}
    seen_machine_codes: dict[
        tuple[str, str],
        AlarmCatalogRow,
    ] = {}
    machine_names: dict[str, str] = {}

    for csv_file in csv_files:
        with csv_file.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            columns = set(reader.fieldnames or [])
            missing_columns = REQUIRED_COLUMNS - columns

            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(
                    f"{csv_file.name}: faltan columnas: {missing}"
                )

            for line_number, raw_row in enumerate(
                reader,
                start=2,
            ):
                values = {
                    column: (raw_row.get(column) or "").strip()
                    for column in REQUIRED_COLUMNS
                }

                empty_columns = [
                    column
                    for column, value in values.items()
                    if not value
                ]

                if empty_columns:
                    empty = ", ".join(sorted(empty_columns))
                    raise ValueError(
                        f"{csv_file.name}, fila {line_number}: "
                        f"campos vacíos: {empty}"
                    )

                if values["severity"] not in ALLOWED_SEVERITIES:
                    raise ValueError(
                        f"{csv_file.name}, fila {line_number}: "
                        f"severity desconocida: "
                        f"{values['severity']}"
                    )

                row = AlarmCatalogRow(
                    alarm_id=values["alarm_id"],
                    alarm_code=values["alarm_code"],
                    alarm_name=values["alarm_name"],
                    machine_id=values["machine_id"],
                    machine_name=values["machine_name"],
                    tag_id=values["tag_id"],
                    severity=values["severity"],
                    source_file=csv_file.name,
                    source_line=line_number,
                )

                previous_name = machine_names.get(row.machine_id)

                if (
                    previous_name is not None
                    and previous_name != row.machine_name
                ):
                    raise ValueError(
                        f"La máquina {row.machine_id} tiene "
                        f"nombres diferentes: "
                        f"{previous_name!r} y {row.machine_name!r}"
                    )

                machine_names[row.machine_id] = row.machine_name

                if row.alarm_id in seen_alarm_ids:
                    previous = seen_alarm_ids[row.alarm_id]
                    raise ValueError(
                        f"alarm_id duplicado {row.alarm_id}: "
                        f"{previous.source_file}:"
                        f"{previous.source_line} y "
                        f"{row.source_file}:{row.source_line}"
                    )

                business_key = (
                    row.machine_id,
                    row.alarm_code,
                )

                if business_key in seen_machine_codes:
                    previous = seen_machine_codes[business_key]
                    raise ValueError(
                        f"Alarma duplicada "
                        f"{row.machine_id}/{row.alarm_code}: "
                        f"{previous.source_file}:"
                        f"{previous.source_line} y "
                        f"{row.source_file}:{row.source_line}"
                    )

                seen_alarm_ids[row.alarm_id] = row
                seen_machine_codes[business_key] = row
                rows.append(row)

    return rows





#esta función obtiene o crea una máquina en la base de datos según el external_id y el nombre proporcionados. Si la máquina no existe, se crea una nueva entrada; si existe pero el nombre es diferente, se actualiza el nombre.
def get_or_create_machine(
    session: Session,
    external_id: str,
    name: str,
) -> tuple[MachineORM, bool]:
    stmt = select(MachineORM).where(
        MachineORM.external_id == external_id
    )

    machine = session.execute(
        stmt
    ).scalar_one_or_none()

    created = False

    if machine is None:
        machine = MachineORM(
            external_id=external_id,
            name=name,
        )

        # El modelo actual espera un PLC por máquina.
        machine.plc = PLCORM(sensors=[])

        session.add(machine)
        session.flush()
        created = True
    elif machine.name != name:
        machine.name = name

    return machine, created



#esta función inserta o actualiza una definición de alarma en la base de datos. Verifica si la definición ya existe por external_alarm_id o por la combinación de machine_id y alarm_code. Si existe, actualiza los campos si es necesario; si no, crea una nueva entrada. También maneja conflictos y asegura que no se cambien las relaciones existentes.
def upsert_alarm_definition(
    session: Session,
    machine: MachineORM,
    row: AlarmCatalogRow,
) -> str:
    by_external_id = session.execute(
        select(AlarmDefinitionORM).where(
            AlarmDefinitionORM.external_alarm_id
            == row.alarm_id
        )
    ).scalar_one_or_none()

    by_business_key = session.execute(
        select(AlarmDefinitionORM).where(
            AlarmDefinitionORM.machine_id == machine.id,
            AlarmDefinitionORM.alarm_code == row.alarm_code,
        )
    ).scalar_one_or_none()

    if (
        by_external_id is not None
        and by_business_key is not None
        and by_external_id.id != by_business_key.id
    ):
        raise ValueError(
            f"Conflicto entre alarm_id {row.alarm_id} "
            f"y la clave "
            f"{row.machine_id}/{row.alarm_code}"
        )

    definition = by_external_id or by_business_key

    if definition is None:
        definition = AlarmDefinitionORM(
            external_alarm_id=row.alarm_id,
            machine_id=machine.id,
            alarm_code=row.alarm_code,
            alarm_name=row.alarm_name,
            tag_id=row.tag_id,
            severity=row.severity,
        )
        session.add(definition)
        return "created"

    # No permitimos mover un alarm_id a otra máquina o código.
    if (
        definition.machine_id != machine.id
        or definition.alarm_code != row.alarm_code
    ):
        raise ValueError(
            f"{row.alarm_id} ya está relacionado con "
            f"otra máquina o código"
        )

    new_values = (
        row.alarm_name,
        row.tag_id,
        row.severity,
    )

    current_values = (
        definition.alarm_name,
        definition.tag_id,
        definition.severity,
    )

    if new_values == current_values:
        return "unchanged"

    definition.alarm_name = row.alarm_name
    definition.tag_id = row.tag_id
    definition.severity = row.severity

    return "updated"



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
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path("data/alarm_catalogs"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    session = SessionLocal()

    try:
        result = import_alarm_catalogs(
            session=session,
            directory=args.directory,
        )

        if args.dry_run:
            session.rollback()
            print("Validación correcta. No se guardaron cambios.")
        else:
            session.commit()
            print("Importación completada.")

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()