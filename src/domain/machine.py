import logging
from enum import Enum
logger = logging.getLogger(__name__)

class MachineStatus(Enum):
    ONLINE = "ONLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class Machine:
    def __init__(self, name:str):
        self.name = name
        self.status =  MachineStatus.ONLINE
        self.error_code = None

    def trigger_error(self, error_code: str):
        self.status = MachineStatus.ERROR
        self.error_code = error_code
        logger.error(f"Machine {self.name} triggered error {self.error_code}")

    def trigger_maintenance(self, fixer: str):
        self.status = MachineStatus.MAINTENANCE
        logger.warning(f"Machine {self.name} triggered maintenance by {fixer}")

    def trigger_online(self):
        self.status = MachineStatus.ONLINE
        self.error_code = None
        logger.info(f"Machine {self.name} triggered online")