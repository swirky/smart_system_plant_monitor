from sensors.sensor_base import Sensor
import adafruit_bh1750      
import board
import random, time
import smbus2

class LightSensor(Sensor):
    def __init__(self, model, address = 0x23):
        super().__init__("Light sensor",model)
        self.model = model
        self.address = address
        i2c = board.I2C()
        self.sensor = adafruit_bh1750.BH1750(i2c,address=address)

    def read(self):
        bus = smbus2.SMBus(1)  # Uruchomienie magistrali I2C (numer 1 dla Raspberry Pi)
        bus.write_byte(0x23, 0x10)  # Wysyłamy polecenie do czujnika
        data = bus.read_i2c_block_data(self.address, 0x10, 2)  # Odczyt 2 bajtów danych
        light_level = (data[0] << 8) | data[1]  # Złożenie dwóch bajtów w jedną wartość
        light_level = round(light_level / 1.2, 1)  # Przeliczenie na luks (1.2 to przelicznik dla BH1750) i zaokroglenie do 1 miejsca po przecinku
        return {'model': self.model, 'lux': light_level, 'timestamp': self.get_current_timestamp()}


    

