from sqlalchemy import Column, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.storage.connectors.postgresql import Base


class AlarmDefinitionORM(Base):
    __tablename__ = "alarm_definitions"

    id = Column(Integer, primary_key=True)
    external_alarm_id = Column(String, nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    sensor_id = Column(
        Integer,
        ForeignKey("sensors.id", name="fk_alarm_definitions_sensor_id"),
        nullable=True,
    )
    alarm_code = Column(String, nullable=False)
    alarm_name = Column(String, nullable=False)
    tag_id = Column(String, nullable=False)
    component = Column(String, nullable=True)
    severity = Column(String, nullable=False)

    machine = relationship("MachineORM", back_populates="alarm_definitions")
    sensor = relationship("SensorORM", back_populates="alarm_definitions")
    alarm_events = relationship("AlarmORM", back_populates="definition")

    __table_args__ = (
        UniqueConstraint("external_alarm_id", name="uq_alarm_definitions_external_alarm_id"),
        UniqueConstraint("machine_id", "alarm_code", name="uq_alarm_definitions_machine_code"),
        Index("ix_alarm_definitions_machine_tag", "machine_id", "tag_id"),
    )
