from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.storage.connectors.postgresql import Base

class PLCORM(Base):
    __tablename__ = "plcs"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("machines.id"))
    owner = relationship("MachineORM", back_populates="plc")
    sensors = relationship("SensorORM", back_populates="owner")
