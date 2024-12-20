import random
from simulated_sensors.simulated_sensor_base import SimulatedSensor


class SimulatedSoilTemperatureSensor(SimulatedSensor):
    def __init__(self, name, model):
        super().__init__("soil temperature sensor", name,
                         model, measurement_types=["soil temperature"])

    def read(self):
        temperature = round(random.uniform(20.0, 22.0), 1)
        return {self.measurement_types[0]: temperature}
