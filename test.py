import time
import board
from adafruit_seesaw.seesaw import Seesaw

# Konfiguracja czujnika
i2c_bus = board.I2C()  # Używa board.SCL i board.SDA
ss = Seesaw(i2c_bus, addr=0x36)

def get_average_moisture():
    moisture_values = []
    for _ in range(20):
        moisture = ss.moisture_read()  # Odczyt wilgotności co 1 sekundę
        moisture_values.append(moisture)
        time.sleep(1)
    avg_moisture = sum(moisture_values) / len(moisture_values)  # Obliczanie średniej
    return avg_moisture

print(get_average_moisture())