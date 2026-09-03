from src.domain.alarm import Alarm
from src.storage.repositories.alarm_definition_repository import (
    AlarmDefinitionRepository,
)
from src.storage.repositories.alarm_repository import (
    AlarmRepository,
)


class AlarmEventService:
    def __init__(
        self,
        definition_repository: AlarmDefinitionRepository,
        alarm_repository: AlarmRepository,
    ):
        self.definition_repository = definition_repository
        self.alarm_repository = alarm_repository

    def activate(
        self,
        machine_id: str,
        alarm_code: str,
        tag_id: str | None = None,
        raw_payload: dict[str, object] | None = None,
    ) -> bool:
        definition = (
            self.definition_repository
            .get_by_machine_and_code(
                machine_external_id=machine_id,
                alarm_code=alarm_code,
            )
        )

        if definition is None:
            raise ValueError(
                "Alarma no incluida en el catálogo: "
                f"{machine_id}/{alarm_code}"
            )

        if (
            tag_id is not None
            and tag_id != definition.tag_id
        ):
            raise ValueError(
                f"El tag {tag_id} no coincide con el "
                f"catálogo para {machine_id}/{alarm_code}"
            )

        alarm = Alarm(
            sensor_id=None,
            machine_id=definition.machine_id,
            alarm_definition_id=definition.definition_id,
            error_code=definition.alarm_code,
            raw_payload=raw_payload,
        )

        inserted = self.alarm_repository.save([alarm])

        return inserted == 1

    def clear(
        self,
        machine_id: str,
        alarm_code: str,
    ) -> Alarm | None:
        definition = (
            self.definition_repository
            .get_by_machine_and_code(
                machine_external_id=machine_id,
                alarm_code=alarm_code,
            )
        )

        if definition is None:
            raise ValueError(
                "Alarma no incluida en el catálogo: "
                f"{machine_id}/{alarm_code}"
            )

        return (
            self.alarm_repository
            .resolve_active_by_definition(
                definition.definition_id
            )
        )