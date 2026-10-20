from random import Random
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.app import App
from src.domain.alarm_definition import AlarmDefinition
from src.domain.machine import Machine, MachineStatus
from src.domain.plc import PLC
from src.domain.sensor import Sensor


def make_machine(active=False):
    definition = AlarmDefinition(
        definition_id=11, external_alarm_id="ALM-DEN-0001", machine_id=1,
        alarm_code="DEN-0001", alarm_name="Pérdida de vacío",
        tag_id="DEN.GRIPPER.VACUUM_LOW", severity="ERROR", sensor_id=7,
    )
    sensor = Sensor(
        name=definition.tag_id, sensor_id=7,
        sensor_type="GRIPPER", definitions=[definition],
    )
    if active:
        sensor.current_errors = {"DEN-0001"}
    return Machine(
        "Denester", PLC([sensor], machine_id=1, plc_id=3),
        machine_id=1, external_id="DENESTER-01", has_active_alarms=active,
    )


def make_app():
    state = SimpleNamespace(now=0.0, active=False)
    app = App(Mock(), interval_seconds=10, rng=Random(42), clock=lambda: state.now)
    app.machine_repo = Mock()
    app.machine_repo.list_all.side_effect = lambda: [make_machine(state.active)]

    def activate(**kwargs):
        assert kwargs["sensor_id"] == 7
        assert kwargs["machine_id"] == "DENESTER-01"
        assert kwargs["alarm_code"] == "DEN-0001"
        if state.active:
            return False
        state.active = True
        return True

    app.events = Mock()
    app.events.activate.side_effect = activate
    return app, state


def test_respects_interval_without_real_sleep():
    app, state = make_app()
    state.now = 9.9
    assert app.update() is False
    app.machine_repo.list_all.assert_not_called()
    state.now = 10
    assert app.update() is True
    state.now = 19.9
    assert app.update() is False
    assert app.events.activate.call_count == 1


def test_active_alarm_not_duplicated_and_resolution_is_reloaded():
    app, state = make_app()
    state.now = 10
    assert app.update() is True
    previous_machine = app.machines[0]
    assert previous_machine.status == MachineStatus.ERROR
    state.now = 20
    assert app.update() is False
    assert app.events.activate.call_count == 1
    # Simula que otro proceso (la API) la ha resuelto en la BD.
    state.active = False
    state.now = 30
    assert app.update() is True
    assert app.machines[0] is not previous_machine
    assert app.events.activate.call_count == 2


def test_restart_reads_active_state():
    app, state = make_app()
    state.active = True
    state.now = 10
    assert app.update() is False
    app.events.activate.assert_not_called()


def test_machine_plc_sensor_proposes_only_linked_catalog_alarm():
    machine = make_machine()
    alarm, = machine.monitor(sensor_id=7, rng=Random(1))
    assert (alarm.machine_id, alarm.sensor_id, alarm.alarm_definition_id) == (1, 7, 11)
    assert alarm.error_code == "DEN-0001"


def test_legacy_sensor_does_not_invent_catalog_codes():
    sensor = Sensor(name="Antiguo", error_codes=["NEUMATIC-001"], sensor_id=99)
    assert sensor.check_sensor() is None


def test_alarm_without_sensor_still_sets_machine_error():
    machine = Machine("Legacy", PLC([]), has_active_alarms=True)
    assert machine.status == MachineStatus.ERROR


@pytest.mark.parametrize("interval", [0, -1, float("nan"), float("inf")])
def test_invalid_interval(interval):
    with pytest.raises(ValueError, match="positivo finito"):
        App(Mock(), interval_seconds=interval)


def test_group_sensor_selects_only_its_non_active_codes():
    definitions = [
        AlarmDefinition(
            definition_id=index, external_alarm_id=f"ALM-{code}", machine_id=1,
            alarm_code=code, alarm_name=code, tag_id=f"DEN.STACK.{suffix}",
            severity="ERROR", sensor_id=8, sensor_type="STACK",
        )
        for index, (code, suffix) in enumerate([
            ("DEN-0004", "LEVEL_LOW"),
            ("DEN-0005", "EMPTY"),
            ("DEN-0021", "CHAIN_WEAR_DETECTED"),
        ], start=1)
    ]
    sensor = Sensor(name="STACK", sensor_type="STACK", sensor_id=8, definitions=definitions)
    sensor.current_errors = {"DEN-0004"}
    assert {item.alarm_code for item in sensor.available_definitions} == {"DEN-0005", "DEN-0021"}
    selected = sensor.check_sensor(Random(42))
    assert selected.alarm_code in {"DEN-0005", "DEN-0021"}
    assert selected.tag_id.startswith("DEN.STACK.")
    sensor.current_errors = {item.alarm_code for item in definitions}
    assert sensor.check_sensor() is None


@pytest.mark.parametrize("tag,expected", [
    ("PONTIA.LACO01.DENE01.STACK.LEVEL_LOW", "STACK"),
    ("PONTIA.LACO01.DENE01.STACK.EMPTY", "STACK"),
    ("PONTIA.LACO01.DENE01.AXIS_Z.SERVO_FAULT", "AXIS_Z"),
    ("PONTIA.LACO01.DENE01.TRAY.JAM_DETECTED", "TRAY"),
])
def test_sensor_type_is_extracted_from_csv_tag(tag, expected):
    from src.storage.importers.alarm_catalog_importer import sensor_type_from_tag

    assert sensor_type_from_tag(tag) == expected


@pytest.mark.parametrize("tag", ["", "STACK", "DEN..EMPTY", "DEN.STACK."])
def test_invalid_tag_is_rejected(tag):
    from src.storage.importers.alarm_catalog_importer import sensor_type_from_tag

    with pytest.raises(ValueError, match="tag_id inválido"):
        sensor_type_from_tag(tag)
