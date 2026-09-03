from datetime import datetime, timezone
import enum


class AlarmStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SOLVED = "SOLVED"

class Alarm:
    def __init__(
            self,
            sensor_id : int | None,
            error_code : str,
            status=AlarmStatus.ACTIVE,
            machine_id: int | None = None,
            triggered_at: datetime | None = None,
            resolved_at: datetime | None = None,
            alarm_id: int | None = None,
            alarm_definition_id: int | None = None,
            raw_payload: dict[str, object] | None = None,
    ):
        self.alarm_id = alarm_id
        self.sensor_id = sensor_id
        self.error_code = error_code
        self.status = status
        self.machine_id = machine_id
        self.triggered_at = triggered_at or datetime.now(timezone.utc)
        self.resolved_at = resolved_at
        self.alarm_definition_id = alarm_definition_id
        self.raw_payload = raw_payload