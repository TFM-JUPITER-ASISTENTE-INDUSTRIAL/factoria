from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas.alarm_schema import AlarmDefinitionResponse
from src.storage.repositories.alarm_definition_repository import AlarmDefinitionRepository

router = APIRouter(prefix="/alarm-definitions", tags=["alarm-definitions"])


@router.get("", response_model=list[AlarmDefinitionResponse])
def get_definitions(
    machine_id: int | None = None,
    sensor_id: int | None = None,
    db: Session = Depends(get_db),
):
    return AlarmDefinitionRepository(db).list_all(machine_id=machine_id, sensor_id=sensor_id)