from abc import ABC, abstractmethod

class Sensor(ABC):
    def __init__(self,type, name, model, measurement_types=[]):
        self.type = type
        self.name = name
        self.model = model
        self.measurement_types = measurement_types
        self.timestamp = None

    @abstractmethod
    def read(self):
        pass


