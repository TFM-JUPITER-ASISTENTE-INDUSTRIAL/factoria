from sqlalchemy import ARRAY, Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.storage.connectors.postgresql import Base


class SensorORM(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("plcs.id"))
    # Nullable para conservar sensores antiguos que no proceden del catálogo.
    tag_id = Column(String, nullable=True)  # Solo compatibilidad con la primera propuesta.
    sensor_type = Column(String, nullable=True)  # STACK, TRAY, etc., procedente del CSV.
    error_codes = Column(ARRAY(String))
    failure_probability = Column(Float)

    owner = relationship("PLCORM", back_populates="sensors")
    alarm_definitions = relationship("AlarmDefinitionORM", back_populates="sensor")

    __table_args__ = (
        UniqueConstraint("owner_id", "tag_id", name="uq_sensors_plc_tag"),
        UniqueConstraint("owner_id", "sensor_type", name="uq_sensors_plc_type"),
    )
