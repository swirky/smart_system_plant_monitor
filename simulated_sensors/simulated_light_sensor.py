import random
from simulated_sensors.simulated_sensor_base import SimulatedSensor


class SimulatedLightSensor(SimulatedSensor):
    def __init__(self, name, model):
        super().__init__("light sensor", name, model,
                         measurement_types=["light intensity"])

    def read(self):
        lux = round(random.uniform(50.0, 150.0), 1)
        return {self.measurement_types[0]: lux}
