from sensors.sensor_base import Sensor
from adafruit_seesaw.seesaw import Seesaw
import board

class SoilHumiditySensor(Sensor):
    def __init__(self,name,model,address=None):
        super().__init__("soil humidity sensor",name,model,measurement_types=["soil humidity"])
        i2c_bus = board.I2C()
        self.address = address
        self.ss = Seesaw(i2c_bus,self.address)

    def read(self):
        moisture = self.ss.moisture_read()
        return {self.measurement_types[0]:moisture}

