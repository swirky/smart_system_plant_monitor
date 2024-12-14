from sensors.sensor_base import Sensor
import board, time
import Adafruit_DHT


class AirTemperatureHumiditySensor(Sensor):
    def __init__(self, name, model, gpio=None):
        super().__init__("air temperature and humidity sensor", name, model,
                         measurement_types=["air temperature", "air humidity"])
        self.sensor = Adafruit_DHT.DHT11
        self.gpio = gpio

    def read(self):
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.gpio)
        if humidity is None or temperature is None:
            print({f"zmienna humidity lub temperature jest none po probie odczytu"})
        else:
            return {self.measurement_types[0]: temperature, self.measurement_types[1]: humidity}
