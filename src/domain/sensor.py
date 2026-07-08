import random

class Sensor:
    def __init__(self, name: str, failure_probability: float, error_codes: list[str]):
        self.name = name
        self.failure_probability = failure_probability
        self.error_codes = error_codes

    def check_sensor(self):
        if random.random() < self.failure_probability:
            return random.choice(self.error_codes) if self.error_codes else "ERR-GENERIC"
        return None

class NeumaticSensor(Sensor):
    def __init__(self):
        super().__init__(
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
    def __init__(self):
        super().__init__(
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
    def __init__(self):
        super().__init__(
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
    def create_sensor(name: str) -> Sensor:
        """ Create sensor correct instance """
        if name == "Neumatic Sensor":
            return NeumaticSensor()
        elif name == "Electric Sensor":
            return ElectricSensor()
        elif name == "Software PLC":
            return SoftwareSensor()
        else:
            raise ValueError(f"Unknown sensor type: {name}")