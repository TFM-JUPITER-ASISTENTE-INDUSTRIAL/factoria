from src.domain.alarm import Alarm, AlarmStatus
from src.domain.sensor import Sensor

class PLC:
    def __init__(self, sensors: list[Sensor] = None, machine_id: int | None = None):
        self.sensors = sensors if sensors is not None else []
        self.machine_id = machine_id

    def add_sensors(self, sensors: list[Sensor]):
        self.sensors.extend(sensors)

    def monitor_plc(self) -> list[Alarm]:
        alarms = []
        for sensor in self.sensors:
            for code in sensor.check_sensor():
                alarms.append(
                    Alarm(sensor_id=sensor.sensor_id,
                          error_code=code,
                          status=AlarmStatus.ACTIVE,
                          machine_id=self.machine_id)
                )
        return alarms