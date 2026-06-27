import random


class PLC:
    def __init__(self, name: str, failure_probability: float, error_codes: list[str]):
        self.name = name
        self.failure_probability = failure_probability
        self.error_codes = error_codes

    def check_sensors(self):
        if random.random() < self.failure_probability:
            return random.choice(self.error_codes) if self.error_codes else "ERR-GENERIC"
        return None

class NeumaticPLC(PLC):
    def __init__(self):
        super().__init__(
            name="Neumatic PLC",
            failure_probability=0.01,
            error_codes=
            [
                "NEUMATIC-001",
                "NEUMATIC-002",
                "NEUMATIC-003"
            ]
        )

class ElectricPLC(PLC):
    def __init__(self):
        super().__init__(
            name="Electric PLC",
            failure_probability=0.02,
            error_codes=
            [
                "ELECTRIC-001",
                "ELECTRIC-002",
                "ELECTRIC-003"
            ]
        )

class SoftwarePLC(PLC):
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


