from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.alarm_definition import AlarmDefinition
from src.storage.entities.alarm_definition_orm import AlarmDefinitionORM
from src.storage.entities.machine_orm import MachineORM


class AlarmDefinitionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_external_id(self, external_alarm_id: str) -> AlarmDefinition | None:
        row = self.session.scalar(select(AlarmDefinitionORM).where(
            AlarmDefinitionORM.external_alarm_id == external_alarm_id,
        ))
        return self._to_domain(row) if row is not None else None

    def get_by_machine_and_code(self, machine_external_id: str,
                               alarm_code: str) -> AlarmDefinition | None:
        row = self.session.scalar(
            select(AlarmDefinitionORM).join(AlarmDefinitionORM.machine).where(
                MachineORM.external_id == machine_external_id,
                AlarmDefinitionORM.alarm_code == alarm_code,
            )
        )
        return self._to_domain(row) if row is not None else None

    def list_by_machine_and_tag(self, machine_external_id: str,
                                tag_id: str) -> list[AlarmDefinition]:
        rows = self.session.scalars(
            select(AlarmDefinitionORM).join(AlarmDefinitionORM.machine).where(
                MachineORM.external_id == machine_external_id,
                AlarmDefinitionORM.tag_id == tag_id,
            ).order_by(AlarmDefinitionORM.id)
        )
        return [self._to_domain(row) for row in rows]

    def list_all(self, machine_id: int | None = None,
                 sensor_id: int | None = None) -> list[AlarmDefinition]:
        stmt = select(AlarmDefinitionORM).order_by(AlarmDefinitionORM.id)
        if machine_id is not None:
            stmt = stmt.where(AlarmDefinitionORM.machine_id == machine_id)
        if sensor_id is not None:
            stmt = stmt.where(AlarmDefinitionORM.sensor_id == sensor_id)
        return [self._to_domain(row) for row in self.session.scalars(stmt)]

    @staticmethod
    def _to_domain(row: AlarmDefinitionORM) -> AlarmDefinition:
        return AlarmDefinition(
            definition_id=row.id,
            external_alarm_id=row.external_alarm_id,
            machine_id=row.machine_id,
            alarm_code=row.alarm_code,
            alarm_name=row.alarm_name,
            tag_id=row.tag_id,
            severity=row.severity,
            sensor_id=row.sensor_id,
            component=row.component,
        )
