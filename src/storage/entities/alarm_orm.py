from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.domain.alarm import AlarmStatus
from src.storage.connectors.postgresql import Base


class AlarmORM(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    alarm_definition_id = Column(
        Integer,
        ForeignKey("alarm_definitions.id", name="fk_alarms_alarm_definition_id"),
        nullable=True,
    )
    error_code = Column(String, nullable=False)
    status = Column(Enum(AlarmStatus, name="alarm_status"), default=AlarmStatus.ACTIVE, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    raw_payload = Column(JSONB, nullable=True)

    definition = relationship("AlarmDefinitionORM", back_populates="alarm_events")
    machine = relationship("MachineORM")
    sensor = relationship("SensorORM")

    __table_args__ = (
        Index(
            "unique_alarms_sensor_code_active", "sensor_id", "error_code",
            unique=True, postgresql_where=text("status = 'ACTIVE'"),
        ),
        Index(
            "unique_active_alarm_definition", "alarm_definition_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE' AND alarm_definition_id IS NOT NULL"),
        ),
    )
