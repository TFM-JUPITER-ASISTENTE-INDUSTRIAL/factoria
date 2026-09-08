import random

from domain.alarm_definition import AlarmDefinition

class Sensor:
    def __init__(
            self,
            name: str,
            failure_probability: float,
            error_codes: list[str],
            sensor_id: int | None = None,
            tag_id: str | None = None,
            definitions: list[AlarmDefinition] | None = None,
    ):
        self.sensor_id = sensor_id
        self.name = name
        self.failure_probability = failure_probability
        self.error_codes = error_codes
        self.tag_id = tag_id
        self.tag_id = tag_id
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

class NeumaticSensor(Sensor):
    def __init__(self, sensor_id: int | None = None):
        super().__init__(
            sensor_id = sensor_id,
            name="Neumatic Sensor",
            failure_probability=0.01,
            error_codes=
            [
                "NEUMATIC-001",
                "NEUMATIC-002",
                "NEUMATIC-003"
            ]
        )

class ElectricSensor(Sensor):
    def __init__(self, sensor_id: int | None = None):
        super().__init__(
            sensor_id = sensor_id,
            name="Electric Sensor",
            failure_probability=0.02,
            error_codes=
            [
                "ELECTRIC-001",
                "ELECTRIC-002",
                "ELECTRIC-003"
            ]
        )

class SoftwareSensor(Sensor):
    def __init__(self, sensor_id: int | None = None):
        super().__init__(
            sensor_id = sensor_id,
            name="Software PLC",
            failure_probability=0.05,
            error_codes=
            [
                "SOFTWARE-001",
                "SOFTWARE-002",
                "SOFTWARE-003"
            ]
        )

class SensorFactory:
    @staticmethod
    def create_sensor(name: str, sensor_id: int | None = None) -> Sensor:
        """ Create sensor correct instance """
        if name == "Neumatic Sensor":
            return NeumaticSensor(sensor_id = sensor_id)
        elif name == "Electric Sensor":
            return ElectricSensor(sensor_id = sensor_id)
        elif name == "Software PLC":
            return SoftwareSensor(sensor_id = sensor_id)
        else:
            raise ValueError(f"Unknown sensor type: {name}")