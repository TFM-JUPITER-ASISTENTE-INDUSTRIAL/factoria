from datetime import datetime, timezone
import enum


class AlarmStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SOLVED = "SOLVED"

class Alarm:
    def __init__(
            self,
            sensor_id,
            error_code,
            status=AlarmStatus.ACTIVE,
            triggered_at = None,
            resolved_at = None,
    ):
        self.sensor_id = sensor_id
        self.error_code = error_code
        self.status = status
        self.triggered_at = triggered_at or datetime.now(timezone.utc)
        self.resolved_at = resolved_at