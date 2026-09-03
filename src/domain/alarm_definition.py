from dataclasses import dataclass


@dataclass(frozen=True)
class AlarmDefinition:
    definition_id: int
    external_alarm_id: str
    machine_id: int
    alarm_code: str
    alarm_name: str
    tag_id: str
    severity: str