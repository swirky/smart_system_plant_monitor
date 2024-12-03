from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from dbmodels import db
from simulated_sensors.simulated_light_sensor import SimulatedLightSensor
from simulated_sensors.simulated_soil_temperature_sensor import SimulatedSoilTemperatureSensor
from simulated_sensors.simulated_air_temperature_humidity_sensor import SimulatedAirTemperatureHumidity
from simulated_sensors.simulated_soil_humidity_sensor import SimulatedSoilHumiditySensor
#real sensor files
# from sensors.light_sensor import LightSensor
# from sensors.soil_temperature_sensor import SoilTemperatureSensor
# from sensors.air_temperature_humidity_sensor import AirTemperatureHumiditySensor
# from sensors.soil_humidity_sensor import SoilHumiditySensor
import sensor_utils

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321@192.168.1.20/monitor_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321%40@127.0.0.1/monit_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins='*')
db.init_app(app)
# ----------------------------Obiekty inicjalizacja---------------------------------------------

simulated_light_sensor_object = SimulatedLightSensor("Light Sensor 1","BH1750")
simulated_soil_temperature_sensor = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 1","DS18B20")
simulated_soil_temperature_sensor2 = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 2","DS18B20")
simulated_air_temperature_humidity_sensor = SimulatedAirTemperatureHumidity("Air Temperature and Humidity Sensor 1", "DHT11")
simulated_soil_humidity_sensor = SimulatedSoilHumiditySensor("Soil Humidity Sensor 1","STEMMA Adafruit")
# light_sensor_object = LightSensor("Light Sensor 1", "BH1750", 0x23)
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
    simulated_light_sensor_object,
    simulated_soil_temperature_sensor,
    simulated_soil_temperature_sensor2,
    simulated_air_temperature_humidity_sensor,
    simulated_soil_humidity_sensor
    # light_sensor_object,
    # soil_temperature_sensor,
    # soil_temperature_sensor2,
    # air_temperature_humidity_sensor,
    # soil_humidity_sensor
]

#zmienne globalne
last_sensor_data = None
active_clients = 0

def wait_for_next_minute():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    time_to_wait = (next_minute - now).total_seconds()
    socketio.sleep(time_to_wait)

def emit_sensor_data(data):
    socketio.emit('sensor_data',data)
    print("Dane zapisane do bazy oraz wysłane do klienta:",last_sensor_data)   

def emit_server_time():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        socketio.emit('server_time', {'time': now})
        socketio.sleep(1)  # Odświeżanie co sekundę

def collect_sensor_data():
    global last_sensor_data
    global active_clients
    with app.app_context():
        while True:
            try:
                wait_for_next_minute()
                last_sensor_data,timestamp = sensor_utils.read_sensor_data(sensor_objects)
                
                if active_clients > 0:
                    socketio.emit('sensor_data',last_sensor_data)
                print("Liczba klientów:", active_clients)
                sensor_utils.save_to_database(last_sensor_data,timestamp)
            except Exception as e:
                print(f"Error during data collection: {e}")


@app.route('/')
def main_panel():
    return render_template('main_panel.html')


@app.route('/historic_data_charts')
def historic_data_charts():
    return render_template('historic_data_charts.html')


@socketio.on('connect')
def on_connect():
    print("Client connected")
    global active_clients
    active_clients +=1
    if last_sensor_data:
        socketio.emit('sensor_data', last_sensor_data)
        print("Wysłano ostatnie dostępne dane do nowego klienta:", last_sensor_data)

@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")
    global active_clients
    active_clients = active_clients-1


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tworzy wszystkie tabele, jeśli jeszcze nie istnieją
        sensor_utils.initialize_sensors(sensor_objects)  # Inicjalizacja czujników
    socketio.start_background_task(target=collect_sensor_data)
    socketio.start_background_task(target=emit_server_time)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
