import random, time
from datetime import datetime
from simulated_sensors.simulated_sensor_base import SimulatedSensor

class SimulatedSoilTemperatureSensor(SimulatedSensor):
    def __init__(self, name, model):
        super().__init__("soil temperature sensor",name, model, measurement_types=["soil temperature"] )
    

    def read(self):
        """Symulacja odczytu temperatury gleby"""
        temperature = round(random.uniform(-10.0, 40.0), 1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {self.measurement_types[0]: temperature}