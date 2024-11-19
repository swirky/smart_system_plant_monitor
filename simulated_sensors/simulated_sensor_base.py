# sensor_base.py
from abc import ABC, abstractmethod
from datetime import datetime

class SimulatedSensor(ABC):
    """
    Klasa bazowa dla wszystkich symulowanych czujników
    """
    def __init__(self,type, name, model, measurement_types=[]):
        self.type = type
        self.name = name
        self.model = model
        self.measurement_types = measurement_types
        self.timestamp = None

    @abstractmethod
    def read(self):
        """
        Metoda abstrakcyjna do odczytu danych z czujnika
        """
        pass

    def get_current_timestamp(self):
        """
        Zwraca aktualny znacznik czasu
        """
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.timestamp
