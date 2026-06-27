import logging
import time

from src.domain.machine import Machine
from src.domain.plcs import NeumaticPLC, ElectricPLC, SoftwarePLC

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
        self.machines = [
            Machine(
                name= "Turbine-A",
                plc_list=[NeumaticPLC()]),
            Machine(
                name= "Compressor-B",
                plc_list=[NeumaticPLC(),ElectricPLC()]),
            Machine(
                name= "Robotic-Harm-C",
                plc_list=[NeumaticPLC(),ElectricPLC(), SoftwarePLC()]),
            Machine(
                name= "Transport-D",
                plc_list=[ElectricPLC(), SoftwarePLC()])
        ]

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

