from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AlarmStatus(Enum):
    ACTIVE = "ACTIVE"
    SOLVED = "SOLVED"


@dataclass
class Alarm:
    sensor_id: int | None
    error_code: str
    status: AlarmStatus = AlarmStatus.ACTIVE
    machine_id: int | None = None
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    alarm_id: int | None = None
    alarm_definition_id: int | None = None
    raw_payload: dict[str, object] | None = None
    # Datos de lectura del catálogo; no se duplican en la tabla alarms.
    machine_name: str | None = None
    machine_external_id: str | None = None
    sensor_name: str | None = None
    external_alarm_id: str | None = None
    alarm_name: str | None = None
    tag_id: str | None = None
    severity: str | None = None
    component: str | None = None
    sensor_type: str | None = None
