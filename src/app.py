import logging
import time

from src.domain.machine import Machine

logger = logging.getLogger(__name__)

machine_names = [
    "Turbine-A",
    "Compressor-B",
    "Robotic-Harm-C"
    "Transport-D"
]

class App:
    def __init__(self):
        self.running = True
        self.ticks = 0
        self.machines = [Machine(name) for name in machine_names]

    def run(self):
        logger.info(msg="FactorIA start")
        while self.running:
            time.sleep(1)
            self.update()

    def update(self):
        self.ticks += 1

        if self.ticks % 60 == 0:
            logger.info(msg=f"FactorIA started after {self.ticks // 60} minutes")

    def stop(self):
        self.running = False

