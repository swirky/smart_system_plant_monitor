from sensors.sensor_base import Sensor
import adafruit_bh1750      
import board
import random, time

class LightSensor(Sensor):
    def __init__(self, model, address = 0x23):
        super().__init__("Light sensor",model)
        self.model = model
        i2c = board.I2C()
        self.sensor = adafruit_bh1750.BH1750(i2c,address=address)

    def read(self):
        "Odczyt natężenia światła w luxach"
        lux = self.sensor.lux
        self.timestamp = self.get_current_timestamp()
        time.sleep(10)  # Odczyt co 10 sekund
        return {'model': self.model, 'lux': lux, 'timestamp': self.timestamp}
    

