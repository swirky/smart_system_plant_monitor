import random, time
from datetime import datetime

class SimulatedLightSensor:
    def __init__(self, model="BH1750"):
        self.model = model

    def read(self):
        """Symulacja odczytu natężenia światła w luxach"""
        lux = round(random.uniform(100.0, 1000.0), 2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {'model': self.model, 'lux': lux, 'timestamp': timestamp}