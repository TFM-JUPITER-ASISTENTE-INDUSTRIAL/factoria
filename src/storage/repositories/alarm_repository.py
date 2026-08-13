from sqlalchemy import text, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from src.Exceptions.database_exception import DatabaseException
from src.domain.alarm import Alarm, AlarmStatus
from src.storage.entities.alarm_orm import AlarmORM


class AlarmRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, alarms: list[Alarm]) -> int:
        if not alarms:
            return 0
        stmt = insert(AlarmORM).values([
            {
                "sensor_id": a.sensor_id,
                "machine_id": a.machine_id,
                "error_code" : a.error_code,
                "status" : a.status.value,
                "triggered_at" : a.triggered_at,
                "resolved_at" : a.resolved_at,
            }
            for a in alarms
        ]).on_conflict_do_nothing(
            index_elements=[
                "sensor_id",
                "error_code",
            ],
            index_where=text(f"status = '{AlarmStatus.ACTIVE.value}'")
        ).returning(AlarmORM.id)

        try:
            result = self.session.execute(stmt)
            self.session.commit()
            return len(result.all())
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseException(
                message="Error al guardar alarmas.",
                original_exception=e)

    def list_active(self) -> list[Alarm]:
        stmt = select(AlarmORM).where(AlarmORM.status == AlarmStatus.ACTIVE)
        alarms_db = self.session.execute(stmt).scalars().all()
        return [self._to_domain(alarm) for alarm in alarms_db]

    def _to_domain(self, alarm_db: AlarmORM) -> Alarm:
        return Alarm(
            sensor_id=alarm_db.sensor_id,
            machine_id=alarm_db.machine_id,  # ← nueva
            error_code=alarm_db.error_code,
            status=alarm_db.status,
            triggered_at=alarm_db.triggered_at,
            resolved_at=alarm_db.resolved_at,
        )