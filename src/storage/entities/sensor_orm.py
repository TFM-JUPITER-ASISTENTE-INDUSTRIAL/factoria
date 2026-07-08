from sqlalchemy import  Column, ForeignKey, Integer, Float, String, ARRAY
from sqlalchemy.orm import relationship
from src.storage.connectors.postgresql import Base

class SensorORM(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("plcs.id"))
    error_codes = Column(ARRAY(String))
    failure_probability = Column(Float)

    owner = relationship("PLCORM", back_populates="sensors")