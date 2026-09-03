from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.alarm_definition import AlarmDefinition
from src.storage.entities.alarm_definition_orm import (
    AlarmDefinitionORM,
)
from src.storage.entities.machine_orm import MachineORM


class AlarmDefinitionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_external_id(
        self,
        external_alarm_id: str,
    ) -> Optional[AlarmDefinition]:
        stmt = select(AlarmDefinitionORM).where(
            AlarmDefinitionORM.external_alarm_id
            == external_alarm_id
        )

        definition_db = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if definition_db is None:
            return None

        return self._to_domain(definition_db)

    def get_by_machine_and_code(
        self,
        machine_external_id: str,
        alarm_code: str,
    ) -> Optional[AlarmDefinition]:
        stmt = (
            select(AlarmDefinitionORM)
            .join(
                MachineORM,
                AlarmDefinitionORM.machine_id
                == MachineORM.id,
            )
            .where(
                MachineORM.external_id
                == machine_external_id,
                AlarmDefinitionORM.alarm_code
                == alarm_code,
            )
        )

        definition_db = self.session.execute(
            stmt
        ).scalar_one_or_none()

        if definition_db is None:
            return None

        return self._to_domain(definition_db)

    def list_by_machine_and_tag(
        self,
        machine_external_id: str,
        tag_id: str,
    ) -> list[AlarmDefinition]:
        stmt = (
            select(AlarmDefinitionORM)
            .join(
                MachineORM,
                AlarmDefinitionORM.machine_id
                == MachineORM.id,
            )
            .where(
                MachineORM.external_id
                == machine_external_id,
                AlarmDefinitionORM.tag_id == tag_id,
            )
        )

        definitions_db = self.session.execute(
            stmt
        ).scalars().all()

        return [
            self._to_domain(definition_db)
            for definition_db in definitions_db
        ]

    @staticmethod
    def _to_domain(
        definition_db: AlarmDefinitionORM,
    ) -> AlarmDefinition:
        return AlarmDefinition(
            definition_id=definition_db.id,
            external_alarm_id=(
                definition_db.external_alarm_id
            ),
            machine_id=definition_db.machine_id,
            alarm_code=definition_db.alarm_code,
            alarm_name=definition_db.alarm_name,
            tag_id=definition_db.tag_id,
            severity=definition_db.severity,
        )