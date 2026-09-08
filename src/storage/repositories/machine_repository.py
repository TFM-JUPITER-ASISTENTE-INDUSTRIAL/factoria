from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from src.Exceptions.database_exception import DatabaseException
from src.domain.alarm import AlarmStatus
from src.domain.machine import Machine
from src.domain.plc import PLC
from src.domain.sensor import Sensor
from src.storage.entities.alarm_orm import AlarmORM
from src.storage.entities.machine_orm import MachineORM
from src.storage.entities.plc_orm import PLCORM
from src.storage.entities.sensor_orm import SensorORM
from src.storage.repositories.alarm_definition_repository import AlarmDefinitionRepository


class MachineRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, machine: Machine) -> MachineORM:
        # Alta de una máquina; el catálogo se importa con el seed.
        machine_db = MachineORM(name=machine.name, external_id=machine.external_id)
        machine_db.plc = PLCORM(sensors=[
            SensorORM(
                name=sensor.name,
                sensor_type=sensor.sensor_type,
                failure_probability=sensor.failure_probability,
                error_codes=sensor.error_codes,
            )
            for sensor in machine.sensors
        ])
        try:
            self.session.add(machine_db)
            self.session.commit()
            return machine_db
        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseException(
                "Error al guardar la máquina", original_exception=error,
            )

    def _load(self, *filters) -> list[Machine]:
        stmt = (
            select(MachineORM).where(*filters).order_by(MachineORM.id)
            .options(
                selectinload(MachineORM.plc)
                .selectinload(PLCORM.sensors)
                .selectinload(SensorORM.alarm_definitions)
            )
            .execution_options(populate_existing=True)
        )
        rows = list(self.session.scalars(stmt))
        if not rows:
            return []
        active = list(self.session.scalars(select(AlarmORM).where(
            AlarmORM.machine_id.in_([row.id for row in rows]),
            AlarmORM.status == AlarmStatus.ACTIVE,
        ).execution_options(populate_existing=True)))
        return [
            self._to_domain(row, [alarm for alarm in active if alarm.machine_id == row.id])
            for row in rows
        ]

    def list_all(self) -> list[Machine]:
        return self._load()

    def get_by_id(self, machine_id: int) -> Machine | None:
        machines = self._load(MachineORM.id == machine_id)
        return machines[0] if machines else None

    def get_by_name(self, name: str) -> Machine | None:
        machines = self._load(MachineORM.name == name)
        return machines[0] if machines else None

    def _to_domain(self, row, active_alarms) -> Machine:
        sensors = []
        for stored in row.plc.sensors if row.plc else []:
            definitions = [
                AlarmDefinitionRepository._to_domain(definition)
                for definition in sorted(stored.alarm_definitions, key=lambda item: item.id)
            ]
            definition_ids = {definition.definition_id for definition in definitions}
            sensor = Sensor(
                name=stored.name,
                sensor_id=stored.id,
                sensor_type=stored.sensor_type,
                failure_probability=stored.failure_probability or 0.0,
                error_codes=stored.error_codes or [],
                definitions=definitions,
            )
            sensor.current_errors = {
                alarm.error_code for alarm in active_alarms
                if alarm.sensor_id == stored.id
                or alarm.alarm_definition_id in definition_ids
            }
            sensors.append(sensor)
        return Machine(
            name=row.name,
            machine_id=row.id,
            external_id=row.external_id,
            has_active_alarms=bool(active_alarms),
            plc=PLC(
                sensors=sorted(sensors, key=lambda sensor: sensor.sensor_id),
                machine_id=row.id,
                plc_id=row.plc.id if row.plc else None,
            ),
        )
