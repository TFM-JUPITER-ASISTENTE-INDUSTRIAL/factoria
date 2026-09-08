from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.domain.alarm import AlarmStatus

class AlarmResponse(BaseModel):
    alarm_id: int
    sensor_id: int | None = None
    machine_id: int
    machine_name: str | None = None
    machine_external_id: str | None = None
    sensor_name: str | None = None
    alarm_definition_id: int | None = None
    external_alarm_id: str | None = None
    error_code: str
    alarm_name: str | None = None
    tag_id: str | None = None
    severity: str | None = None
    component: str | None = None
    status: AlarmStatus
    triggered_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class AlarmDefinitionResponse(BaseModel):
    definition_id: int
    external_alarm_id: str
    machine_id: int
    sensor_id: int | None = None
    alarm_code: str
    alarm_name: str
    tag_id: str
    component: str | None = None
    severity: str

    model_config = ConfigDict(from_attributes=True)