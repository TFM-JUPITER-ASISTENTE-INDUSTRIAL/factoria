from src.Exceptions.plc_exception import PLCException
from src.domain.sensor import Sensor

class PLC:
    def __init__(self, sensors: list[Sensor] = None):
        self.sensors = sensors if sensors is not None else []
        self.error_codes = {sensor.name: [] for sensor in self.sensors}

    def monitor_plc(self):
        has_new_error = False
        for sensor in self.sensors:
            error_code = sensor.check_sensor()
            if error_code:
                if error_code not in self.error_codes[sensor.name]:
                    self.error_codes[sensor.name].append(error_code)
                    has_new_error = True
        if has_new_error:
            raise PLCException("Se detectaron errores en los sensores del PLC", self.error_codes)