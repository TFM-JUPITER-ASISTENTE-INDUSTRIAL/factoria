from pydantic import BaseModel, ConfigDict
from src.domain.machine import MachineStatus

class SensorResponse(BaseModel):
    sensor_id: int | None = None
    name: str
    failure_probability: float
    current_errors: list[str] = []

    model_config = ConfigDict(from_attributes=True)

class MachineResponse(BaseModel):
    machine_id: int | None = None
    name: str
    status: MachineStatus
    sensors: list[SensorResponse] = []

    model_config = ConfigDict(from_attributes=True)