import time
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify

from dbmodels import db, SensorType, MeasurementType, SensorTypeCapabilities, Sensor, SensorReading
from simulated_sensors.simulated_light_sensor import SimulatedLightSensor
from simulated_sensors.simulated_soil_temperature_sensor import SimulatedSoilTemperatureSensor
from simulated_sensors.simulated_air_temperature_humidity_sensor import SimulatedAirTemperatureHumidity
from simulated_sensors.simulated_soil_humidity_sensor import SimulatedSoilHumiditySensor
# real sensor files
# from sensors.light_sensor import LightSensor
# from sensors.soil_temperature_sensor import SoilTemperatureSensor
# from sensors.air_temperature_humidity_sensor import AirTemperatureHumiditySensor
# from sensors.soil_humidity_sensor import SoilHumiditySensor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321@192.168.1.20/monitor_db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321%40@127.0.0.1/monit_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# ----------------------------Obiekty inicjalizacja---------------------------------------------

simulated_light_sensor = SimulatedLightSensor("Light Sensor 1","BH1750")
simulated_soil_temperature_sensor = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 1","DS18B20")
simulated_soil_temperature_sensor2 = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 2","DS18B20")
simulated_air_temperature_humidity_sensor = SimulatedAirTemperatureHumidity("Air Temperature and Humidity Sensor 1", "DHT11")
simulated_soil_humidity_sensor = SimulatedSoilHumiditySensor("Soil Humidity Sensor 1","STEMMA Adafruit")
# light_sensor = LightSensor("Light Sensor 1", "BH1750", 0x23)
# soil_temperature_sensor = SoilTemperatureSensor(
#     "Soil Temperature Sensor 1", "DS18B20", "28-0623b2e1cc75")
# soil_temperature_sensor2 = SoilTemperatureSensor(
#     "Soil Temperature Sensor 2", "DS18B20", "28-307ad4432e60")
# air_temperature_humidity_sensor = AirTemperatureHumiditySensor(
#     "Air Temperature and Humidity Sensor 1", "DHT11", 13)
# soil_humidity_sensor = SoilHumiditySensor(
#     "Soil Humidity Sensor 1", "STEMMA Adafruit", 0x36)
# ----------------------------------------------------------------------------------------------

sensor_objects = [
    simulated_light_sensor,
    simulated_soil_temperature_sensor,
    simulated_soil_temperature_sensor2,
    simulated_air_temperature_humidity_sensor,
    simulated_soil_humidity_sensor
    # light_sensor,
    # soil_temperature_sensor,
    # soil_temperature_sensor2,
    # air_temperature_humidity_sensor,
    # soil_humidity_sensor
]

last_sensor_data = {
    "Light Sensor 1": {"light intensity": 0},
    "Soil Temperature Sensor 1": {"soil temperature": 0},
    "Soil Temperature Sensor 2": {"soil temperature": 0},
    "Air Temperature and Humidity Sensor 1": {"air temperature": 0, "air humidity": 0},
    "Soil Humidity Sensor 1": {"soil humidity": 0}
}

def add_sensor_or_sensor_type_if_not_exists(sensor_object):
    sensor_type = SensorType.query.filter_by(name=sensor_object.type).first()
    if not sensor_type:
        sensor_type = SensorType(name=sensor_object.type)
        db.session.add(sensor_type)
        db.session.commit()
        print("Sensor type added")
    sensor = Sensor.query.filter_by(
        name=sensor_object.name, model=sensor_object.model).first()
    if not sensor:
        sensor = Sensor(name=sensor_object.name,
                        model=sensor_object.model, type_id=sensor_type.id)
        db.session.add(sensor)
        db.session.commit()
        print("Sensor added")

     # Dodanie możliwości pomiarowych dla czujnika
    for measurement_name in sensor_object.measurement_types:
        # Znajdź lub dodaj typ pomiaru
        measurement_type = MeasurementType.query.filter_by(
            name=measurement_name).first()
        if not measurement_type:
            measurement_type = MeasurementType(name=measurement_name)
            db.session.add(measurement_type)
            db.session.commit()

        # Dodaj powiązanie między typem czujnika a typem pomiaru
        capability = SensorTypeCapabilities.query.filter_by(
            sensor_type_id=sensor_type.id,
            measurement_type_id=measurement_type.id
        ).first()
        if not capability:
            capability = SensorTypeCapabilities(
                sensor_type_id=sensor_type.id, measurement_type_id=measurement_type.id)
            db.session.add(capability)
            db.session.commit()
    return sensor


def add_sensor_reading(sensor, reading_value):
    reading = SensorReading(sensor_id=sensor.id, value=reading_value)
    db.session.add(reading)
    db.session.commit()


def initialize_sensors():
    for sensor_object in sensor_objects:
        add_sensor_or_sensor_type_if_not_exists(sensor_object)


# Funkcja do zczytywania danych co pełną minutę
def collect_sensor_data():
    global last_sensor_data
    with app.app_context():
        while True:
            try:
                # Czekanie do pełnej minuty
                now = datetime.now()
                next_minute = (now + timedelta(minutes=1)
                               ).replace(second=0, microsecond=0)
                time_to_wait = (next_minute - now).total_seconds()
                time.sleep(time_to_wait)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                last_sensor_data = {}

                for sensor_object in sensor_objects:
                    data = sensor_object.read()

                    if sensor_object.name not in last_sensor_data:
                        last_sensor_data[sensor_object.name] = {}
                    for measurement_type_name, value in data.items():
                        last_sensor_data[sensor_object.name][measurement_type_name] = value


                for sensor_name, measurements in last_sensor_data.items():
                    # szuka czujnika w bazie
                    sensor = Sensor.query.filter_by(name=sensor_name).first()
                    for measurement_type_name, value in measurements.items():
                        measurement_type = MeasurementType.query.filter_by(
                            name=measurement_type_name).first()

                        # Dodaj odczyt do tabeli sensor_readings
                        reading = SensorReading(
                            sensor_id=sensor.id,
                            measurement_type_id=measurement_type.id,
                            value=value,
                            timestamp=timestamp
                        )
                        db.session.add(reading)
                # zatwierdzenie zapisow w bazie
                db.session.commit()

            except Exception as e:
                print(f"Error during data collection: {e}")


@app.route('/')
def main_panel():
    return render_template('main_panel.html')


@app.route('/historic_data_charts')
def historic_data_charts():
    return render_template('historic_data_charts.html')


@app.route('/stream')
def stream():
    def generate():
        with app.app_context():
            previous_data = None  # Śledzenie poprzednich danych
            while True:
                try:
                    if last_sensor_data != previous_data:  # Wysyłaj tylko, jeśli dane się zmieniły
                        previous_data = last_sensor_data.copy()
                        print(f"Przesyłanie danych: {last_sensor_data}")
                        yield f"data: {jsonify(last_sensor_data).get_data(as_text=True)}\n\n"
                    time.sleep(1)  # Krótkie odświeżanie, aby reagować szybko na zmiany
                except Exception as e:
                    yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    return app.response_class(generate(), content_type='text/event-stream')

@app.route('/chart-stream')
def chart_stream():
    def generate_chart_data():
        with app.app_context():
            last_timestamp = None  # Śledzenie ostatniego przesłanego punktu danych
            while True:
                try:
                    # Pobierz najnowsze dane z bazy
                    latest_data = SensorReading.query.order_by(SensorReading.timestamp.desc()).all()
                    if latest_data:
                        # Sprawdź, czy są nowe dane
                        new_timestamp = latest_data[0].timestamp
                        if new_timestamp != last_timestamp:
                            last_timestamp = new_timestamp
                            # Sformatuj dane w strukturę wykresu
                            chart_data = [
                                {
                                    "sensor_id": reading.sensor_id,
                                    "measurement_type_id": reading.measurement_type_id,
                                    "value": reading.value,
                                    "timestamp": reading.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                } for reading in latest_data
                            ]
                            # Wyślij dane do klienta
                            yield f"data: {jsonify(chart_data).get_data(as_text=True)}\n\n"
                    time.sleep(1)  # Czekaj sekundę przed ponownym sprawdzeniem bazy
                except Exception as e:
                    yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    return app.response_class(generate_chart_data(), content_type='text/event-stream')
 

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tworzy wszystkie tabele, jeśli jeszcze nie istnieją
        initialize_sensors()  # Inicjalizacja czujników
    import threading
    threading.Thread(target=collect_sensor_data, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)

