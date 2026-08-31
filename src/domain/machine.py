import logging
from enum import Enum

from src.domain.alarm import Alarm
from src.domain.plc import PLC

logger = logging.getLogger(__name__)

class MachineStatus(Enum):
    ONLINE = "ONLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class Machine:
    def __init__(self, name:str, plc:PLC, machine_id:int | None = None):
        self.name = name
        self.plc = plc
        self.machine_id = machine_id

    def monitor(self) -> list[Alarm]:
        return self.plc.monitor_plc()

    @property
    def status(self) -> MachineStatus:
        has_errors = any(sensor.current_errors for sensor in self.plc.sensors)
        return MachineStatus.ERROR if has_errors else MachineStatus.ONLINE

    def log_status(self):
        logger.info(f"Machine {self.name} is {self.status.value}")
