from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.Exceptions.database_exception import DatabaseException
from src.domain.machine import Machine
from src.domain.plc import PLC
from src.domain.sensor import SensorFactory
from src.storage.entities.machine_orm import MachineORM
from src.storage.entities.plc_orm import PLCORM
from src.storage.entities.sensor_orm import SensorORM


class MachineRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, machine: Machine)-> Optional[MachineORM]:
        """ Save Machine to DB """
        machine_db = MachineORM(name=machine.name)
        sensors_db = [
            SensorORM(
                name= s.name,
                failure_probability=s.failure_probability,
                error_codes=s.error_codes
            )
            for s in machine.plc.sensors
        ]
        plc_db = PLCORM(sensors = sensors_db)
        machine_db.plc = plc_db
        try:
            self.session.add(machine_db)
            self.session.commit()
            return machine_db
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseException(
                f"Error al guardar la máquina {machine.name} en la base de datos",
                original_exception=e
            )

    def get_by_id(self, machine_id: int) -> Optional[Machine]:
        """ Get Machine by id from DB """
        stmt = select(MachineORM).where(MachineORM.id == machine_id)
        machine_db = self.session.execute(stmt).scalar_one_or_none()
        if machine_db is None:
            return None
        return self._to_domain(machine_db)

    def get_by_name(self, name:str) -> Optional[Machine]:
        """ Get Machine by name from DB """
        stmt = select(MachineORM).where(MachineORM.name == name)
        machine_db = self.session.execute(stmt).scalar_one_or_none()
        if machine_db is None:
            return None
        return self._to_domain(machine_db)

    def list_all(self) -> list[Machine]:
        stmt = select(MachineORM)
        all_machines_db = self.session.execute(stmt).scalars().all()
        return [self._to_domain(machine_db) for machine_db in all_machines_db]

    def _to_domain(self, machine_db: MachineORM) -> Machine:
        """ Convert MachineORM to Machine """
        sensors = [
            SensorFactory.create_sensor(sensor.name, sensor.id)
            for sensor in machine_db.plc.sensors
        ]
        plc = PLC(sensors=sensors, machine_id=machine_db.id)
        machine = Machine(machine_id=machine_db.id, name=machine_db.name, plc=plc)
        return machine


