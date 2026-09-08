from src.domain.alarm import Alarm
from src.domain.sensor import Sensor


class PLC:
    def __init__(
        self,
        sensors: list[Sensor] | None = None,
        machine_id: int | None = None,
        plc_id: int | None = None,
    ):
        self.sensors = list(sensors or [])
        self.machine_id = machine_id
        self.plc_id = plc_id

    def add_sensors(self, sensors: list[Sensor]):
        self.sensors.extend(sensors)

    def monitor_plc(self, sensor_id: int, rng=None) -> list[Alarm]:
        for sensor in self.sensors:
            if sensor.sensor_id != sensor_id:
                continue
            definition = sensor.check_sensor(rng=rng)
            if definition is None:
                return []
            if (
                definition.sensor_id != sensor.sensor_id
                or definition.machine_id != self.machine_id
            ):
                raise ValueError("La definición no pertenece a este sensor/máquina")
            return [Alarm(
                sensor_id=sensor.sensor_id,
                machine_id=self.machine_id,
                alarm_definition_id=definition.definition_id,
                error_code=definition.alarm_code,
                tag_id=definition.tag_id,
                sensor_type=sensor.sensor_type,
            )]
        raise ValueError(f"Sensor {sensor_id} no encontrado en el PLC")
