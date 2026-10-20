import pytest

from src.domain.alarm import Alarm, AlarmStatus
from src.domain.alarm_definition import AlarmDefinition
from src.services.alarm_event_service import AlarmEventService
from src.storage.repositories.alarm_repository import AlarmRepository


class FakeDefinitionRepository:
    def __init__(self, definition: AlarmDefinition | None):
        self.definition = definition
        self.calls: list[tuple[str, str]] = []

    def get_by_machine_and_code(
        self,
        machine_external_id: str,
        alarm_code: str,
    ) -> AlarmDefinition | None:
        self.calls.append((machine_external_id, alarm_code))
        return self.definition


class FakeAlarmRepository:
    def __init__(
        self,
        inserted: int = 1,
        resolved_alarm: Alarm | None = None,
    ):
        self.inserted = inserted
        self.resolved_alarm = resolved_alarm
        self.saved: list[Alarm] = []
        self.resolved_definition_ids: list[int] = []

    def save(self, alarms: list[Alarm]) -> int:
        self.saved.extend(alarms)
        return self.inserted

    def resolve_active_by_definition(
        self,
        alarm_definition_id: int,
    ) -> Alarm | None:
        self.resolved_definition_ids.append(alarm_definition_id)
        return self.resolved_alarm


@pytest.fixture
def definition() -> AlarmDefinition:
    return AlarmDefinition(
        definition_id=27,
        sensor_id=12,
        external_alarm_id="ALM-DEN-0001",
        machine_id=1,
        alarm_code="DEN-0001",
        alarm_name="Perdida de vacio",
        tag_id="PONTIA.LACO01.DENE01.GRIPPER.VACUUM_LOW",
        severity="ERROR",
    )


def test_activate_creates_catalog_linked_alarm(definition):
    definitions = FakeDefinitionRepository(definition)
    alarms = FakeAlarmRepository(inserted=1)
    service = AlarmEventService(definitions, alarms)
    payload = {"active": True, "source": "PLC"}

    created = service.activate(
        machine_id="DENESTER-01",
        alarm_code="DEN-0001",
        tag_id=definition.tag_id,
        raw_payload=payload,
    )

    assert created is True
    assert definitions.calls == [("DENESTER-01", "DEN-0001")]
    assert len(alarms.saved) == 1

    event = alarms.saved[0]
    assert event.sensor_id == definition.sensor_id
    assert event.machine_id == definition.machine_id
    assert event.alarm_definition_id == definition.definition_id
    assert event.error_code == definition.alarm_code
    assert event.status == AlarmStatus.ACTIVE
    assert event.raw_payload == payload


def test_activate_returns_false_when_active_event_already_exists(definition):
    definitions = FakeDefinitionRepository(definition)
    alarms = FakeAlarmRepository(inserted=0)
    service = AlarmEventService(definitions, alarms)

    created = service.activate(
        machine_id="DENESTER-01",
        alarm_code="DEN-0001",
    )

    assert created is False
    assert len(alarms.saved) == 1


def test_activate_rejects_unknown_alarm():
    definitions = FakeDefinitionRepository(None)
    alarms = FakeAlarmRepository()
    service = AlarmEventService(definitions, alarms)

    with pytest.raises(ValueError, match="no incluida en el catálogo"):
        service.activate(
            machine_id="DENESTER-01",
            alarm_code="DEN-9999",
        )

    assert alarms.saved == []


def test_activate_rejects_mismatched_tag(definition):
    definitions = FakeDefinitionRepository(definition)
    alarms = FakeAlarmRepository()
    service = AlarmEventService(definitions, alarms)

    with pytest.raises(ValueError, match="no coincide"):
        service.activate(
            machine_id="DENESTER-01",
            alarm_code="DEN-0001",
            tag_id="WRONG.TAG",
        )

    assert alarms.saved == []


def test_clear_resolves_active_alarm_by_definition(definition):
    resolved = Alarm(
        alarm_id=9,
        sensor_id=None,
        machine_id=definition.machine_id,
        alarm_definition_id=definition.definition_id,
        error_code=definition.alarm_code,
        status=AlarmStatus.SOLVED,
    )
    definitions = FakeDefinitionRepository(definition)
    alarms = FakeAlarmRepository(resolved_alarm=resolved)
    service = AlarmEventService(definitions, alarms)

    result = service.clear("DENESTER-01", "DEN-0001")

    assert result is resolved
    assert alarms.resolved_definition_ids == [definition.definition_id]


def test_clear_rejects_unknown_alarm():
    definitions = FakeDefinitionRepository(None)
    alarms = FakeAlarmRepository()
    service = AlarmEventService(definitions, alarms)

    with pytest.raises(ValueError, match="no incluida en el catálogo"):
        service.clear("DENESTER-01", "DEN-9999")

    assert alarms.resolved_definition_ids == []


def test_alarm_repository_exposes_definition_resolution_method():
    assert hasattr(AlarmRepository, "resolve_active_by_definition")


def test_activate_rejects_wrong_sensor(definition):
    service = AlarmEventService(FakeDefinitionRepository(definition), FakeAlarmRepository())
    with pytest.raises(ValueError, match="sensor no coincide"):
        service.activate("DENESTER-01", "DEN-0001", sensor_id=999)


def test_activate_rejects_unmapped_definition(definition):
    from dataclasses import replace

    service = AlarmEventService(
        FakeDefinitionRepository(replace(definition, sensor_id=None)),
        FakeAlarmRepository(),
    )
    with pytest.raises(ValueError, match="sin sensor"):
        service.activate("DENESTER-01", "DEN-0001")
