import logging
import time

from sqlalchemy.orm import Session

from src.domain.machine import Machine
from src.domain.plc import PLC
from src.domain.sensor import NeumaticSensor, ElectricSensor, SoftwareSensor
from src.storage.repositories import machine_repository
from src.storage.repositories.machine_repository import MachineRepository

logger = logging.getLogger(__name__)

machine_names = [
    "Turbine-A",
    "Compressor-B",
    "Robotic-Harm-C"
    "Transport-D"
]


class App:
    def __init__(self, session: Session):
        self.running = True
        self.ticks = 0
        repo = MachineRepository(session=session)
        self.machines = repo.list_all()

    def run(self):
        logger.info(msg="FactorIA start")
        while self.running:
            time.sleep(1)
            self.update()

    def update(self):
        self.ticks += 1
        for machine in self.machines:
            machine.monitor()

        if self.ticks % 60 == 0:
            logger.info(msg=f"FactorIA started after {self.ticks // 60} minutes")
            for machine in self.machines:
                machine.log_status()

    def stop(self):
        self.running = False
