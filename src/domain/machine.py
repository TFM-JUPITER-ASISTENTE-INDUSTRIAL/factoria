import logging
from enum import Enum

from src.domain.alarm import Alarm
from src.domain.plc import PLC
from src.domain.sensor import Sensor

logger = logging.getLogger(__name__)

class MachineStatus(Enum):
    ONLINE = "ONLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class Machine:
    def __init__(self, name:str, plc:PLC, machine_id:int | None = None,external_id: str | None = None,has_active_alarms: bool = False,):
        self.name = name
        self.plc = plc
        self.machine_id = machine_id
        self.external_id = external_id
        self.has_active_alarms = has_active_alarms

    def monitor(self, sensor_id: int, rng=None) -> list[Alarm]:
        return self.plc.monitor_plc(sensor_id=sensor_id, rng=rng)

    @property
    def status(self) -> MachineStatus:
        has_errors = self.has_active_alarms or any(
            sensor.current_errors for sensor in self.sensors
        )
        return MachineStatus.ERROR if has_errors else MachineStatus.ONLINE

    @property
    def sensors(self) -> list[Sensor]:
        return self.plc.sensors if self.plc else []

    def log_status(self):
        logger.info("Machine %s is %s", self.name, self.status.value)
