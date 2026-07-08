import logging
from enum import Enum

from src.Exceptions.plc_exception import PLCException
from src.domain.plc import PLC

logger = logging.getLogger(__name__)

class MachineStatus(Enum):
    ONLINE = "ONLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class Machine:
    def __init__(self, name:str, plc:PLC):
        self.name = name
        self.status =  MachineStatus.ONLINE
        self.plc = plc
        self._current_errors = {}

    def monitor(self):
        try:
            self.plc.monitor_plc()
        except PLCException as e:
            self._current_errors = e.errors
            self.trigger_error()

    def log_status(self):
        logger.info(f"Machine {self.name} is {self.status.value}")
        if self.status == MachineStatus.ERROR:
            logger.error(f"Machine {self.name} has errors: {self.plc.error_codes}")

    def trigger_error(self):
        self.status = MachineStatus.ERROR
        logger.error(f"Machine {self.name} has errors: {self.plc.error_codes}")
