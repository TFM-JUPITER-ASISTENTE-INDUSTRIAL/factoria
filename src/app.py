import logging
import time
import os
import random
import time
from sqlalchemy.orm import Session

from src.domain.alarm import Alarm
from src.storage.repositories.alarm_repository import AlarmRepository
from src.storage.repositories.machine_repository import MachineRepository
from storage.repositories.alarm_definition_repository import AlarmDefinitionRepository

logger = logging.getLogger(__name__)

class App:
    def __init__(
        self, session: Session, interval_seconds: float | None = None,
        rng=None, clock=time.monotonic, sleeper=time.sleep,
    ):
        interval = (
            float(os.getenv("SIMULATION_INTERVAL_SECONDS", "10"))
            if interval_seconds is None else float(interval_seconds)
        )
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("SIMULATION_INTERVAL_SECONDS debe ser un número positivo finito")
        self.session = session
        self.interval = interval
        self.clock = clock
        self.sleeper = sleeper
        self.rng = rng or random.Random(os.getenv("SIMULATION_SEED") or None)
        self.next_due = self.clock() + self.interval
        self.running = True
        self.ticks = 0
        self.machines = []
        self.machine_repo = MachineRepository(session)
        self.alarm_repo = AlarmRepository(session)
        self.events = AlarmEventService(AlarmDefinitionRepository(session), self.alarm_repo)

    def run(self):
        logger.info("FactorIA: un fallo nuevo cada %s segundos en toda la planta", self.interval)
        while self.running:
            self.sleeper(max(0.0, self.next_due - self.clock()))
            if self.running:
                self.update()

    def update(self) -> bool:
        now = self.clock()
        if now < self.next_due:
            return False
        self.next_due = now + self.interval
        self.ticks += 1
        # Esta sesión pertenece exclusivamente al simulador.
        # Finalizar la lectura anterior y reconstruir el estado desde BD.
        self.session.rollback()
        self.session.expire_all()
        try:
            self.machines = self.machine_repo.list_all()
            candidates = [
                (machine, sensor)
                for machine in self.machines if machine.external_id
                for sensor in machine.sensors
                if sensor.sensor_id is not None and sensor.available_definitions
            ]
            if not candidates:
                logger.info("Sin fallos elegibles: catálogo vacío o todos activos")
                return False
            machine, sensor = self.rng.choice(candidates)
            alarms = machine.monitor(sensor_id=sensor.sensor_id, rng=self.rng)
            if not alarms:
                return False
            alarm = alarms[0]
            created = self.events.activate(
                machine_id=machine.external_id,
                alarm_code=alarm.error_code,
                sensor_id=sensor.sensor_id,
                tag_id=sensor.tag_id,
                raw_payload={"source": "simulator", "tick": self.ticks},
            )
            if created:
                sensor.current_errors.add(alarm.error_code)
                machine.has_active_alarms = True
                logger.info(
                    "ALARMA máquina=%s sensor=%s tag=%s código=%s",
                    machine.external_id, sensor.sensor_id, sensor.tag_id, alarm.error_code,
                )
            return created
        finally:
            # Libera también transacciones de lectura cuando no hubo inserción.
            self.session.rollback()

    def stop(self):
        self.running = False