import random

from src.domain.alarm_definition import AlarmDefinition


class Sensor:
    def __init__(
        self,
        name: str,
        failure_probability: float = 1.0,
        error_codes: list[str] | None = None,
        sensor_id: int | None = None,
        sensor_type: str | None = None,
        definitions: list[AlarmDefinition] | None = None,
    ):
        self.sensor_id = sensor_id
        self.name = name
        self.sensor_type = sensor_type
        # Conservado para compatibilidad; el modo periódico no utiliza probabilidad.
        self.failure_probability = failure_probability
        self.definitions = list(definitions or [])
        self.error_codes = (
            [definition.alarm_code for definition in self.definitions]
            if self.definitions else list(error_codes or [])
        )
        self.current_errors: set[str] = set()

    @property
    def available_definitions(self) -> list[AlarmDefinition]:
        return [
            definition for definition in self.definitions
            if definition.alarm_code not in self.current_errors
        ]

    def check_sensor(self, rng=None) -> AlarmDefinition | None:
        available = self.available_definitions
        if not available:
            return None
        # Propone un fallo; el servicio confirmará la persistencia.
        return (rng or random).choice(available)

    def fix(self, error_code: str | None = None):
        if error_code is None:
            self.current_errors.clear()
        else:
            self.current_errors.discard(error_code)
