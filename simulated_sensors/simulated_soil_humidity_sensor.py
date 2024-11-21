import random
from simulated_sensors.simulated_sensor_base import SimulatedSensor

class SimulatedSoilHumiditySensor(SimulatedSensor):
    def __init__(self, name, model):
        super().__init__("soil humidity sensor",name, model,measurement_types=["soil humidity"]) 
        
        
    def read(self):
        soil_humidity = round(random.uniform(200.0, 900.0), 1)
        return {self.measurement_types[0]: soil_humidity}