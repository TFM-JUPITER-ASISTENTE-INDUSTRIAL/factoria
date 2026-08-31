from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.domain.alarm import AlarmStatus

class AlarmResponse(BaseModel):
    id: int | None = None
    sensor_id: int | None = None
    machine_id: int | None = None
    machine_name: str | None = None
    error_code: str
    status: AlarmStatus
    triggered_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)