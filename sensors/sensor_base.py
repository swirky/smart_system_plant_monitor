# sensor_base.py
from abc import ABC, abstractmethod
from datetime import datetime

class Sensor(ABC):
    """
    Klasa bazowa dla wszystkich czujników
    """
    def __init__(self, name, model):
        self.name = name
        self.model = model
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
