from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import AlarmResponse, MachineResponse
from src.storage.repositories.machine_repository import MachineRepository

router = APIRouter(prefix="/machines", tags=["machines"])

@router.get("", response_model=list[MachineResponse])
def get_machines(db: Session = Depends(get_db)):
    """Lista todas las maquinas con su estado y sensores"""
    repo = MachineRepository(session=db)
    return repo.list_all()

@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    repo = MachineRepository(session=db)
    machine = repo.get_by_id(machine_id=machine_id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID {machine_id} not found"
        )
    return machine