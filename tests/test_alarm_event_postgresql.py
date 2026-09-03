import os

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from src.domain.alarm import AlarmStatus
from src.services.alarm_event_service import AlarmEventService
from src.storage.entities.alarm_orm import AlarmORM
from src.storage.repositories.alarm_definition_repository import (
    AlarmDefinitionRepository,
)
from src.storage.repositories.alarm_repository import AlarmRepository


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.fixture
def repositories():
    engine = create_engine(TEST_DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    definitions = AlarmDefinitionRepository(session)
    alarms = AlarmRepository(session)

    definition = definitions.get_by_machine_and_code(
        machine_external_id="DENESTER-01",
        alarm_code="DEN-0001",
    )

    assert definition is not None

    session.execute(
        delete(AlarmORM).where(
            AlarmORM.alarm_definition_id
            == definition.definition_id
        )
    )
    session.commit()

    try:
        yield definitions, alarms, definition
    finally:
        session.execute(
            delete(AlarmORM).where(
                AlarmORM.alarm_definition_id
                == definition.definition_id
            )
        )
        session.commit()
        session.close()
        engine.dispose()


def test_catalog_repositories_find_real_definition(repositories):
    definitions, _, expected = repositories

    by_external_id = definitions.get_by_external_id(
        "ALM-DEN-0001"
    )
    by_tag = definitions.list_by_machine_and_tag(
        machine_external_id="DENESTER-01",
        tag_id=expected.tag_id,
    )

    assert by_external_id == expected
    assert by_tag == [expected]


def test_alarm_event_full_postgresql_lifecycle(repositories):
    definitions, alarms, definition = repositories
    service = AlarmEventService(definitions, alarms)
    payload = {
        "machine_id": "DENESTER-01",
        "alarm_code": "DEN-0001",
        "tag_id": definition.tag_id,
        "active": True,
        "source": "integration-test",
    }

    assert service.activate(
        machine_id="DENESTER-01",
        alarm_code="DEN-0001",
        tag_id=definition.tag_id,
        raw_payload=payload,
    ) is True

    active = alarms.get_active_by_definition(
        definition.definition_id
    )

    assert active is not None
    assert active.status == AlarmStatus.ACTIVE
    assert active.sensor_id is None
    assert active.machine_id == definition.machine_id
    assert active.alarm_definition_id == definition.definition_id
    assert active.raw_payload == payload

    assert service.activate(
        machine_id="DENESTER-01",
        alarm_code="DEN-0001",
        tag_id=definition.tag_id,
        raw_payload=payload,
    ) is False

    resolved = service.clear(
        machine_id="DENESTER-01",
        alarm_code="DEN-0001",
    )

    assert resolved is not None
    assert resolved.alarm_id == active.alarm_id
    assert resolved.status == AlarmStatus.SOLVED
    assert resolved.resolved_at is not None
    assert alarms.get_active_by_definition(
        definition.definition_id
    ) is None

    assert service.activate(
        machine_id="DENESTER-01",
        alarm_code="DEN-0001",
        tag_id=definition.tag_id,
        raw_payload=payload,
    ) is True

    history = [
        event
        for event in alarms.list_all(
            machine_id=definition.machine_id
        )
        if event.alarm_definition_id
        == definition.definition_id
    ]

    assert len(history) == 2
    assert sum(
        event.status == AlarmStatus.ACTIVE
        for event in history
    ) == 1
    assert sum(
        event.status == AlarmStatus.SOLVED
        for event in history
    ) == 1
