from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
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
                "alarm_definition_id" : a.alarm_definition_id,
                "raw_payload" : a.raw_payload,
            }
            for a in alarms
        ]).on_conflict_do_nothing().returning(AlarmORM.id)

        try:
            result = self.session.execute(stmt)
            self.session.commit()
            return len(result.all())
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseException(
                message="Error al guardar alarmas.",
                original_exception=e)

    def get_by_id(self, alarm_id: int) -> Optional[Alarm]:
        stmt = select(AlarmORM).where(AlarmORM.id == alarm_id)
        alarm_db = self.session.execute(stmt).scalar_one_or_none()
        if alarm_db is None:
            return None
        return self._to_domain(alarm_db)

    def list_all(self,
                 status: Optional[AlarmStatus] = None,
                 machine_id: Optional[int] = None
                 ) -> list[Alarm]:
        stmt = select(AlarmORM)
        if status is not None:
            stmt = stmt.where(AlarmORM.status == status)
        if machine_id is not None:
            stmt = stmt.where(AlarmORM.machine_id == machine_id)

        alarms_db = self.session.execute(stmt).scalars().all()
        return [self._to_domain(alarm_db) for alarm_db in alarms_db]

    def list_active(self) -> list[Alarm]:
        return self.list_all(status=AlarmStatus.ACTIVE)

    def count_active(self) -> int:
        stmt = select(func.count(AlarmORM.id)).where(AlarmORM.status == AlarmStatus.ACTIVE)
        count = self.session.execute(stmt).scalar()
        return count or 0

    def resolve_alarm(self, alarm_id: int) -> Optional[Alarm]:
        stmt = select(AlarmORM).where(AlarmORM.id == alarm_id)
        alarm_db = self.session.execute(stmt).scalar_one_or_none()
        if alarm_db is None:
            return None
        alarm_db.status = AlarmStatus.SOLVED
        alarm_db.resolved_at = datetime.now(timezone.utc)
        try:
            self.session.commit()
            self.session.refresh(alarm_db)
            return self._to_domain(alarm_db)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseException(
                message=f"Error al resolver la alarma {alarm_id}.",
                original_exception=e
            )

    def _to_domain(self, alarm_db: AlarmORM) -> Alarm:
        return Alarm(
            sensor_id=alarm_db.sensor_id,
            machine_id=alarm_db.machine_id,  # ← nueva
            error_code=alarm_db.error_code,
            status=alarm_db.status,
            triggered_at=alarm_db.triggered_at,
            resolved_at=alarm_db.resolved_at,
            alarm_id=alarm_db.id,
            alarm_definition_id=alarm_db.alarm_definition_id,
            raw_payload=alarm_db.raw_payload,
        )

    def get_active_by_definition(
        self,
        alarm_definition_id: int,
    ) -> Optional[Alarm]:
        stmt = select(AlarmORM).where(
            AlarmORM.alarm_definition_id
            == alarm_definition_id,
            AlarmORM.status == AlarmStatus.ACTIVE,
        )

        alarm_db = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if alarm_db is None:
            return None

        return self._to_domain(alarm_db)

    def resolve_active_by_definition(
        self,
        alarm_definition_id: int,
    ) -> Optional[Alarm]:
        stmt = select(AlarmORM).where(
            AlarmORM.alarm_definition_id
            == alarm_definition_id,
            AlarmORM.status == AlarmStatus.ACTIVE,
        )

        alarm_db = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if alarm_db is None:
            return None

        alarm_db.status = AlarmStatus.SOLVED
        alarm_db.resolved_at = datetime.now(timezone.utc)

        try:
            self.session.commit()
            self.session.refresh(alarm_db)
            return self._to_domain(alarm_db)
        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseException(
                message=(
                    "Error al resolver la alarma activa "
                    f"de la definición {alarm_definition_id}."
                ),
                original_exception=error,
            )
