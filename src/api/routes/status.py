from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import FactoryStatusResponse
from src.domain.machine import MachineStatus
from src.storage.repositories.alarm_repository import AlarmRepository
from src.storage.repositories.machine_repository import MachineRepository

router = APIRouter(prefix="/status", tags=["status"])

@router.get("", response_model=FactoryStatusResponse)
def get_factory_status(db: Session = Depends(get_db)):
    """Devuelve un resumen global del estado de la planta y las alarmas activas"""
    machine_repo = MachineRepository(session=db)
    alarm_repo = AlarmRepository(session=db)

    machines = machine_repo.list_all()
    total_machines = len(machines)
    machines_online = sum(1 for m in machines if m.status == MachineStatus.ONLINE)
    machines_error = sum(1 for m in machines if m.status == MachineStatus.ERROR)
    active_alarms_count = alarm_repo.count_active()

    return FactoryStatusResponse(
        total_machines=total_machines,
        machines_online=machines_online,
        machines_error=machines_error,
        active_alarms_count=active_alarms_count
    )