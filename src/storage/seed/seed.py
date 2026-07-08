from src.storage.connectors.postgresql import SessionLocal
from src.storage.entities.machine_orm import MachineORM
from src.storage.repositories.machine_repository import MachineRepository
from src.domain.machine import Machine
from src.domain.plc import PLC
from src.domain.sensor import NeumaticSensor, ElectricSensor, SoftwareSensor


def seed_database():
    session = SessionLocal()
    repo = MachineRepository(session)

    # 1. Comprobamos si la base de datos ya tiene máquinas
    machine_count = session.query(MachineORM).count()
    if machine_count > 0:
        return

    # 2. Definimos las máquinas por defecto
    machines_to_seed = [
        Machine(
            name="Turbine-A",
            plc=PLC(sensors=[NeumaticSensor()])),
        Machine(name="Compressor-B",
                plc=PLC(sensors=[NeumaticSensor(), ElectricSensor()])),
        Machine(name="Robotic-Harm-C",
                plc=PLC(sensors=[NeumaticSensor(), ElectricSensor(), SoftwareSensor()])),
        Machine(name="Transport-D", plc=PLC(sensors=[ElectricSensor(), SoftwareSensor()]))
    ]
    print("Poblando la base de datos con las máquinas iniciales...")

    # 3. Guardamos cada máquina usando el repositorio
    for machine in machines_to_seed:
        repo.save(machine)

    print("¡Base de datos poblada con éxito!")
    session.close()

if __name__ == "__main__":
    seed_database()
