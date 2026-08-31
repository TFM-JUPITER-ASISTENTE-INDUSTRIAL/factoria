
from src.domain.machine import Machine, MachineStatus

#macjine necesita recibir un PLC
class FakePLC:
    def __init__(self, sensors=None):
        self.sensors = sensors if sensors is not None else []


def test_machine_creation():
    plc = FakePLC()
    machine = Machine("Machine 1", plc)

    assert machine.name == "Machine 1"
    assert machine.status == MachineStatus.ONLINE
    assert machine.plc == plc