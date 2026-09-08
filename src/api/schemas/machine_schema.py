from pydantic import BaseModel, ConfigDict, Field

from src.api.schemas.alarm_schema import AlarmDefinitionResponse
from src.domain.machine import MachineStatus


class SensorResponse(BaseModel):
    sensor_id: int | None = None
    name: str
    tag_id: str | None = None
    failure_probability: float
    current_errors: list[str] = Field(default_factory=list)
    definitions: list[AlarmDefinitionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PLCResponse(BaseModel):
    plc_id: int | None = None
    machine_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class MachineResponse(BaseModel):
    machine_id: int | None = None
    external_id: str | None = None
    name: str
    status: MachineStatus
    plc: PLCResponse
    sensors: list[SensorResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)