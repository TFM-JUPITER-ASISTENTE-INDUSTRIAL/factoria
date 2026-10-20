from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from src.Exceptions.database_exception import DatabaseException
from src.domain.alarm import Alarm, AlarmStatus
from src.storage.entities.alarm_orm import AlarmORM


class AlarmRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _query():
        return select(AlarmORM).options(
            joinedload(AlarmORM.definition),
            joinedload(AlarmORM.machine),
            joinedload(AlarmORM.sensor),
        ).execution_options(populate_existing=True)

    def save(self, alarms: list[Alarm]) -> int:
        if not alarms:
            return 0
        stmt = insert(AlarmORM).values([
            {
                "sensor_id": alarm.sensor_id, "machine_id": alarm.machine_id,
                "error_code": alarm.error_code, "status": alarm.status.value,
                "triggered_at": alarm.triggered_at, "resolved_at": alarm.resolved_at,
                "alarm_definition_id": alarm.alarm_definition_id,
                "raw_payload": alarm.raw_payload,
            }
            for alarm in alarms
        ]).on_conflict_do_nothing().returning(AlarmORM.id)
        try:
            ids = self.session.execute(stmt).scalars().all()
            self.session.commit()
            return len(ids)
        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseException("Error al guardar alarmas", original_exception=error)

    def get_by_id(self, alarm_id: int) -> Alarm | None:
        row = self.session.scalar(self._query().where(AlarmORM.id == alarm_id))
        return self._to_domain(row) if row is not None else None

    def list_all(self, status: AlarmStatus | None = None,
                 machine_id: int | None = None) -> list[Alarm]:
        stmt = self._query().order_by(AlarmORM.triggered_at.desc(), AlarmORM.id.desc())
        if status is not None:
            stmt = stmt.where(AlarmORM.status == status)
        if machine_id is not None:
            stmt = stmt.where(AlarmORM.machine_id == machine_id)
        return [self._to_domain(row) for row in self.session.scalars(stmt)]

    def list_active(self) -> list[Alarm]:
        return self.list_all(status=AlarmStatus.ACTIVE)

    def count_active(self) -> int:
        return self.session.scalar(select(func.count(AlarmORM.id)).where(
            AlarmORM.status == AlarmStatus.ACTIVE,
        )) or 0

    def get_active_by_definition(self, alarm_definition_id: int) -> Alarm | None:
        row = self.session.scalar(self._query().where(
            AlarmORM.alarm_definition_id == alarm_definition_id,
            AlarmORM.status == AlarmStatus.ACTIVE,
        ))
        return self._to_domain(row) if row is not None else None

    def resolve_alarm(self, alarm_id: int) -> Alarm | None:
        # Bloquear solo la fila del evento, sin bloquear los LEFT JOIN del catálogo.
        row = self.session.scalar(
            select(AlarmORM).where(AlarmORM.id == alarm_id)
            .with_for_update().execution_options(populate_existing=True)
        )
        if row is None:
            return None
        return self._resolve(row)

    def resolve_active_by_definition(self, alarm_definition_id: int) -> Alarm | None:
        row = self.session.scalar(
            select(AlarmORM).where(
                AlarmORM.alarm_definition_id == alarm_definition_id,
                AlarmORM.status == AlarmStatus.ACTIVE,
            ).with_for_update().execution_options(populate_existing=True)
        )
        return self._resolve(row) if row is not None else None

    def _resolve(self, row: AlarmORM) -> Alarm:
        try:
            alarm_id = row.id
            if row.status != AlarmStatus.SOLVED:
                row.status = AlarmStatus.SOLVED
                row.resolved_at = datetime.now(timezone.utc)
            # Incluso si ya estaba resuelta, libera el bloqueo sin cambiar la fecha.
            self.session.commit()
            return self.get_by_id(alarm_id)
        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseException("Error al resolver alarma", original_exception=error)

    @staticmethod
    def _to_domain(row: AlarmORM) -> Alarm:
        definition = row.definition
        return Alarm(
            alarm_id=row.id, sensor_id=row.sensor_id,
            machine_id=row.machine_id, error_code=row.error_code,
            status=row.status, triggered_at=row.triggered_at, resolved_at=row.resolved_at,
            alarm_definition_id=row.alarm_definition_id, raw_payload=row.raw_payload,
            machine_name=row.machine.name if row.machine else None,
            machine_external_id=row.machine.external_id if row.machine else None,
            sensor_name=row.sensor.name if row.sensor else None,
            sensor_type=row.sensor.sensor_type if row.sensor else None,
            external_alarm_id=definition.external_alarm_id if definition else None,
            alarm_name=definition.alarm_name if definition else None,
            tag_id=definition.tag_id if definition else None,
            severity=definition.severity if definition else None,
            component=definition.component if definition else None,
        )
