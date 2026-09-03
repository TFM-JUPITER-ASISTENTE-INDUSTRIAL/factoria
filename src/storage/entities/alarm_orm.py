from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, text, Enum

from src.domain.alarm import AlarmStatus
from src.storage.connectors.postgresql import Base

class AlarmORM(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    error_code = Column(String, nullable=False)
    status = Column(
        Enum(AlarmStatus, name="alarm_status"),
        default=AlarmStatus.ACTIVE,
        nullable=False
    )
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "unique_alarms_sensor_code_active",
            "sensor_id",
            "error_code",
            unique=True,
            postgresql_where=text(
                f"status = '{AlarmStatus.ACTIVE.value}'"
            ),
        ),
    )
