import random
from simulated_sensors.simulated_sensor_base import SimulatedSensor


class SimulatedAirTemperatureHumidity(SimulatedSensor):
    def __init__(self, name, model):
        super().__init__("air temperature and humidity sensor", name,
                         model, measurement_types=["air temperature", "air humidity"])

    def read(self):
        air_temperature = round(random.uniform(-10.0, 40.0), 1)
        air_humidity = round(random.uniform(0, 100))
        return {self.measurement_types[0]: air_temperature, self.measurement_types[1]: air_humidity}
