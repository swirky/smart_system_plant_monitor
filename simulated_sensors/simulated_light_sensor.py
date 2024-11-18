import random, time
from datetime import datetime
from simulated_sensors.simulated_sensor_base import SimulatedSensor

class SimulatedLightSensor(SimulatedSensor):
    def __init__(self, name, model):
        super().__init__("light sensor",name, model,measurement_types=["light intensity"]) 
        
        
    def read(self):
        """Symulacja odczytu natężenia światła w luxach"""
        lux = round(random.uniform(100.0, 1000.0), 1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {'model': self.model, 'lux': lux, 'timestamp': timestamp}