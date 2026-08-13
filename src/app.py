import logging
import time

from sqlalchemy.orm import Session

from src.domain.alarm import Alarm
from src.storage.repositories.alarm_repository import AlarmRepository
from src.storage.repositories.machine_repository import MachineRepository

logger = logging.getLogger(__name__)

class App:
    def __init__(self, session: Session):
        self.running = True
        self.ticks = 0
        repo = MachineRepository(session=session)
        self.machines = repo.list_all()
        self.pending_alarms: list[Alarm] = []
        self.alarm_repo = AlarmRepository(session=session)

    def run(self):
        logger.info(msg="FactorIA start")
        while self.running:
            time.sleep(1)
            self.update()

    def update(self):
        self.ticks += 1
        for machine in self.machines:
            self.pending_alarms.extend(machine.monitor())

        if self.pending_alarms:
            self.alarm_repo.save(self.pending_alarms)
            self.pending_alarms.clear()

        if self.ticks % 60 == 0:
            logger.info(msg=f"FactorIA started after {self.ticks // 60} minutes")
            for machine in self.machines:
                machine.log_status()

    def stop(self):
        self.running = False
