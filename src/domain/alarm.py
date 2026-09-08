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
            machine_name: str | None = None,
            machine_external_id: str | None = None,
            sensor_name: str | None = None,
            external_alarm_id: str | None = None,
            alarm_name: str | None = None,
            tag_id: str | None = None,
            severity: str | None = None,
            component: str | None = None


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
        self.machine_name = machine_name
        self.machine_external_id = machine_external_id
        self.sensor_name = sensor_name
        self.external_alarm_id = external_alarm_id
        self.alarm_name = alarm_name
        self.tag_id = tag_id
        self.severity = severity
        self.component = component
