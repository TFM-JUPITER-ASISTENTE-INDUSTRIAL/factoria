class AlarmEventService:
    def __init__(self, definition_repository: AlarmDefinitionRepository,
                 alarm_repository: AlarmRepository):
        self.definition_repository = definition_repository
        self.alarm_repository = alarm_repository

    def _definition(self, machine_id: str, alarm_code: str):
        definition = self.definition_repository.get_by_machine_and_code(
            machine_external_id=machine_id, alarm_code=alarm_code,
        )
        if definition is None:
            raise ValueError(f"Alarma no incluida en el catálogo: {machine_id}/{alarm_code}")
        return definition

    def activate(
        self, machine_id: str, alarm_code: str,
        tag_id: str | None = None,
        raw_payload: dict[str, object] | None = None,
        sensor_id: int | None = None,
    ) -> bool:
        definition = self._definition(machine_id, alarm_code)
        if tag_id is not None and tag_id != definition.tag_id:
            raise ValueError(f"El tag {tag_id} no coincide con el catálogo")
        if definition.sensor_id is None:
            raise ValueError("Definición sin sensor: ejecuta el seed actualizado")
        if sensor_id is not None and sensor_id != definition.sensor_id:
            raise ValueError("El sensor no coincide con el catálogo")
        alarm = Alarm(
            sensor_id=definition.sensor_id,
            machine_id=definition.machine_id,
            alarm_definition_id=definition.definition_id,
            error_code=definition.alarm_code,
            raw_payload=raw_payload,
        )
        return self.alarm_repository.save([alarm]) == 1

    def clear(self, machine_id: str, alarm_code: str) -> Alarm | None:
        definition = self._definition(machine_id, alarm_code)
        return self.alarm_repository.resolve_active_by_definition(definition.definition_id)