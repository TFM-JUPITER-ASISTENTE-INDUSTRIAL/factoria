import logging
from enum import Enum

from src.domain.plcs import PLC

logger = logging.getLogger(__name__)

class MachineStatus(Enum):
    ONLINE = "ONLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class Machine:
    def __init__(self, name:str, plc_list:list[PLC]):
        if plc_list is None:
            plc_list = []
        self.name = name
        self.status =  MachineStatus.ONLINE
        self.plc_list = plc_list
        self.error_codes = {plc.name: [] for plc in self.plc_list}

    def monitor(self):
        for plc in self.plc_list:
            error_code = plc.check_sensors()
            if error_code:
                current_errors = self.error_codes.setdefault(plc.name, [])
                if error_code not in current_errors:
                    self.trigger_error(plc, error_code)
                    current_errors.append(error_code)

    def log_status(self):
        logger.info(f"Machine {self.name} is {self.status.value}")
        if self.status == MachineStatus.ERROR:
            logger.error(f"Machine {self.name} has errors: {self.error_codes}")

    def trigger_error(self, plc: PLC, error_code: str):
        self.status = MachineStatus.ERROR
        logger.error(f"Machine {self.name} PLC {plc.name} triggered error {error_code}")

    def trigger_maintenance(self, fixer: str):
        self.status = MachineStatus.MAINTENANCE
        logger.warning(f"Machine {self.name} triggered maintenance by {fixer}")

    def trigger_online(self):
        self.status = MachineStatus.ONLINE
        for plc in self.plc_list:
            self.error_codes[plc.name] = []
        logger.info(f"Machine {self.name} triggered online")