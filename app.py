import time
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from simulated_sensors.simulated_light_sensor import SimulatedLightSensor
from simulated_sensors.simulated_soil_temperature_sensor import SimulatedSoilTemperatureSensor
from simulated_sensors.simulated_air_temperature_humidity_sensor import SimulatedAirTemperatureHumidity
from simulated_sensors.simulated_soil_humidity_sensor import SimulatedSoilHumiditySensor
from dbmodels import db, SensorType, MeasurementType, SensorTypeCapabilities, Sensor, SensorReading

#from sensors.light_sensor import LightSensor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321@192.168.1.20/monitor_db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321%40@127.0.0.1/monit_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins='*')
db.init_app(app)
#----------------------------Obiekty inicjalizacja---------------------------------------------

simulated_light_sensor_object = SimulatedLightSensor("Light Sensor 1","BH1750")
simulated_soil_temperature_sensor = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 1","DS18B20")
simulated_soil_temperature_sensor2 = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 2","DS18B20")
simulated_air_temperature_humidity_sensor = SimulatedAirTemperatureHumidity("Air Temperature and Humidity Sensor 1", "DHT11")
simulated_soil_humidity_sensor = SimulatedSoilHumiditySensor("Soil Moisture Sensor 1","STEMMA Adafruit")
#lightsensorObj = LightSensor("BH1750")
#----------------------------------------------------------------------------------------------

sensor_objects =[
    simulated_light_sensor_object,
    simulated_soil_temperature_sensor,
    simulated_soil_temperature_sensor2,
    simulated_air_temperature_humidity_sensor,
    simulated_soil_humidity_sensor
]

last_sensor_data = None 

def add_sensor_or_sensor_type_if_not_exists(sensor_object):
    sensor_type = SensorType.query.filter_by(name=sensor_object.type).first()
    if not sensor_type:
        sensor_type = SensorType(name=sensor_object.type)
        db.session.add(sensor_type)
        db.session.commit()
        print("Sensor type added")
    sensor = Sensor.query.filter_by(name=sensor_object.name, model=sensor_object.model).first()
    if not sensor:
        sensor = Sensor(name=sensor_object.name, model=sensor_object.model, type_id=sensor_type.id)
        db.session.add(sensor)
        db.session.commit()
        print("Sensor added")
    
     # Dodanie możliwości pomiarowych dla czujnika
    for measurement_name in sensor_object.measurement_types:
        # Znajdź lub dodaj typ pomiaru
        measurement_type = MeasurementType.query.filter_by(name=measurement_name).first()
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
            capability = SensorTypeCapabilities(sensor_type_id=sensor_type.id, measurement_type_id=measurement_type.id)
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
                next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                time_to_wait = (next_minute - now).total_seconds()
                socketio.sleep(time_to_wait)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                last_sensor_data = {}

                for sensor_object in sensor_objects:
                    data = sensor_object.read()
                    
                    if sensor_object.name not in last_sensor_data:
                        last_sensor_data[sensor_object.name] = {}
                    for measurement_type_name, value in data.items():
                        last_sensor_data[sensor_object.name][measurement_type_name] = value

                socketio.emit('sensor_data', last_sensor_data)
                print("Dane zapisane do bazy oraz wysłane do klienta:", last_sensor_data)


                for sensor_name, measurements in last_sensor_data.items():
                    #szuka czujnika w bazie
                    sensor = Sensor.query.filter_by(name=sensor_name).first()   
                    for measurement_type_name, value in measurements.items():
                        measurement_type = MeasurementType.query.filter_by(name=measurement_type_name).first()

                        # Dodaj odczyt do tabeli sensor_readings
                        reading = SensorReading(
                            sensor_id=sensor.id,
                            measurement_type_id=measurement_type.id,
                            value=value,
                            timestamp=timestamp
                        )
                        db.session.add(reading)       
                #zatwierdzenie zapisow w bazie
                db.session.commit()

            except Exception as e:
                print(f"Error during data collection: {e}")


@app.route('/')
def main_panel():
    return render_template('main_panel.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/light_sensor')
def light_sensor():
    return render_template('light_sensor.html')

@socketio.on('connect')
def on_connect():
    print('Client connected')
    if last_sensor_data:
        socketio.emit('sensor_data', last_sensor_data)   #jednorazowe emitowanie ostatnio dostepnej wartosci z zmiennej globalnej
        print("Wysłano ostatnie dostępne dane do nowego klienta:", last_sensor_data)



if __name__ == '__main__':
    #if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Uruchamiamy zadania w tle tylko w głównym procesie
    with app.app_context():
        db.create_all()  # Tworzy wszystkie tabele, jeśli jeszcze nie istnieją
        initialize_sensors()  # Inicjalizacja czujników
    socketio.start_background_task(target=collect_sensor_data)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
