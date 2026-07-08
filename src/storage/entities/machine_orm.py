from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.storage.connectors.postgresql import Base

class MachineORM(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    plc = relationship("PLCORM", back_populates="owner", uselist=False)