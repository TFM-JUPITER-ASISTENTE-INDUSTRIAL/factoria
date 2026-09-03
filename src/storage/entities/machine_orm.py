from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.storage.connectors.postgresql import Base

class MachineORM(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True)

    # machine_id procedente del CSV
    external_id = Column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )

    # machine_name procedente del CSV
    name = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    #name = Column(String, unique=True, index=True)  -Codigo anterior
    plc = relationship("PLCORM", back_populates="owner", uselist=False)

    alarm_definitions = relationship(
        "AlarmDefinitionORM",
        back_populates="machine",
    )


