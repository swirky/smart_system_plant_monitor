from sensors.sensor_base import Sensor

class SoilTemperatureSensor(Sensor):
    def __init__(self, name, model, device_id=""):
        super().__init__("soil temperature sensor", name, model, measurement_types=["soil temperature"])
        self.device_id = device_id  # Identyfikator urządzenia 1-Wire
        self.device_file = f"/sys/bus/w1/devices/{self.device_id}/w1_slave"

    def read(self):
        with open(self.device_file, 'r') as file:
            lines = file.readlines()

        if "YES" not in lines[0]:
            raise RuntimeError(f"CRC check failed for device {self.device_file}")

        temp_string = lines[1].split("t=")[-1]
        temperature = round(float(temp_string) / 1000.0, 1)
        return {self.measurement_types[0]: temperature}




