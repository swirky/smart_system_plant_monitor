from sensors.sensor_base import Sensor
import adafruit_bh1750
import board
import random, time
import smbus2


class LightSensor(Sensor):
    def __init__(self, name, model, address=0x23):
        super().__init__("light sensor", name, model, measurement_types=["light intensity"])
        self.address = address
        i2c = board.I2C()
        self.sensor = adafruit_bh1750.BH1750(i2c, address=self.address)

    def read(self):
        bus = smbus2.SMBus(1)
        bus.write_byte(0x23, 0x10)
        data = bus.read_i2c_block_data(self.address, 0x10, 2)
        light_level = (data[0] << 8) | data[1]
        light_level = round(light_level / 1.2, 1)
        return {self.measurement_types[0]: light_level}
