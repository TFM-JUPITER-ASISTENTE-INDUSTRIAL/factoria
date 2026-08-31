from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import AlarmResponse
from src.domain.alarm import AlarmStatus
from src.storage.repositories.alarm_repository import AlarmRepository

router = APIRouter(prefix="/alarms", tags=["alarms"])

@router.get("", response_model=list[AlarmResponse])
def get_alarms(
    status: Optional[AlarmStatus] = None,
        machine_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """Lista todas las alarmas con filtros opcionales por estado o máquina"""
    repo = AlarmRepository(session=db)
    return repo.list_all(status=status, machine_id=machine_id)

@router.get("/{alarm_id}", response_model=AlarmResponse)
def get_alarm(alarm_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de una alarma por su ID."""
    repo = AlarmRepository(session=db)
    alarm = repo.get_by_id(alarm_id=alarm_id)
    if alarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with ID {alarm_id} not found"
        )
    return alarm

@router.patch("/{alarm_id}/resolve", response_model=AlarmResponse)
def resolve_alarm(
        alarm_id: int,
        db: Session = Depends(get_db),
):
    """Marca una alarma como resuelta"""
    repo = AlarmRepository(session=db)
    alarm = repo.resolve_alarm(alarm_id=alarm_id)
    if alarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with ID {alarm_id} not found"
        )
    return alarm