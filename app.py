from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request
from flask_socketio import SocketIO
from dbmodels import db
import logging
from flask_mail import Mail
import sensor_utils
import email_notifications
from config import Config
from simulated_sensors.simulated_light_sensor import SimulatedLightSensor
from simulated_sensors.simulated_soil_temperature_sensor import SimulatedSoilTemperatureSensor
from simulated_sensors.simulated_air_temperature_humidity_sensor import SimulatedAirTemperatureHumidity
from simulated_sensors.simulated_soil_humidity_sensor import SimulatedSoilHumiditySensor
#real sensor files
# from sensors.light_sensor import LightSensor
# from sensors.soil_temperature_sensor import SoilTemperatureSensor
# from sensors.air_temperature_humidity_sensor import AirTemperatureHumiditySensor
# from sensors.soil_humidity_sensor import SoilHumiditySensor

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins='*')
db.init_app(app)
mail = Mail(app)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# ----------------------------Objects initialization---------------------------------------------
simulated_light_sensor = SimulatedLightSensor("Light Sensor 1","BH1750")
simulated_soil_temperature_sensor = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 1","DS18B20")
simulated_soil_temperature_sensor2 = SimulatedSoilTemperatureSensor("Soil Temperature Sensor 2","DS18B20")
simulated_air_temperature_humidity_sensor = SimulatedAirTemperatureHumidity("Air Temperature and Humidity Sensor 1", "DHT11")
simulated_soil_humidity_sensor = SimulatedSoilHumiditySensor("Soil Humidity Sensor 1","STEMMA Adafruit")
# light_sensor = LightSensor("Light Sensor 1", "BH1750", 0x23)
# soil_temperature_sensor = SoilTemperatureSensor("Soil Temperature Sensor 1", "DS18B20", "28-0623b2e1cc75")
# soil_temperature_sensor2 = SoilTemperatureSensor("Soil Temperature Sensor 2", "DS18B20", "28-307ad4432e60")
# air_temperature_humidity_sensor = AirTemperatureHumiditySensor("Air Temperature and Humidity Sensor 1", "DHT11", 13)
# soil_humidity_sensor = SoilHumiditySensor("Soil Humidity Sensor 1", "STEMMA Adafruit", 0x36)
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

#zmienne globalne
last_sensor_data = None
active_clients = 0
client_preferences = {}


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


def handle_client_preferences():
    for client_id, prefs in client_preferences.items():
        data = {
            'days': prefs.get('days', 1),
            'hours': prefs.get('hours', 1)
        }
        handle_request_historical_data_with_range(data, client_id)


def collect_sensor_data():
    global last_sensor_data
    global active_clients
    with app.app_context():
        while True:
            try:
                wait_for_next_minute()
                last_sensor_data, timestamp = sensor_utils.get_data_from_sensors(sensor_objects)
                sensor_utils.save_last_data(last_sensor_data, timestamp)
                if active_clients > 0:
                    socketio.emit('sensor_data',last_sensor_data)
                    handle_client_preferences()
                email_notifications.send_alert_emails_for_active_readings()
            except Exception as e:
                logger.error(f"Error during data collection: {e}")


@socketio.on('request_historical_data_with_range')
def handle_request_historical_data_with_range(data, client_id=None):
    try:
        if client_id is None:
            client_id = request.sid
        days = data.get('days', 0)
        hours = data.get('hours', 1)
        client_preferences[client_id] = {'days': days, 'hours': hours}
        historical_data = sensor_utils.get_measurement_with_range(sensor_objects,days,hours)
        thresholds = sensor_utils.get_all_thresholds()
        chart_data = {'historical_data': historical_data,'thresholds': thresholds}
        socketio.emit('historical_data_response',chart_data, to=client_id)
        logger.info("Emitting historical data to client")
    except Exception as e:
        logger.error("Error while handling historical data request: {e}")


@app.route('/')
def main_panel():
    return render_template('main_panel.html')


@app.route('/historic_data_charts')
def historic_data_charts():
    return render_template('historic_data_charts.html')


@app.route('/get_thresholds', methods=['GET'])
def get_thresholds():
    thresholds = sensor_utils.get_all_thresholds()
    return render_template('threshold_config.html', thresholds_data=thresholds)


@app.route('/save_thresholds', methods=['POST'])
def save_thresholds():
    sensor_utils.save_thresholds(request.form)
    flash('Progi alarmowe zostały zapisane!')
    return redirect('/get_thresholds')


@app.route('/get_notification_config_data', methods=['GET'])
def get_notification_config_data():
    email = sensor_utils.get_email_recipients()
    thresholds = sensor_utils.get_all_thresholds()
    return render_template('notification_config.html', email=email, thresholds=thresholds)


@app.route('/save_email', methods=['POST'])
def save_emails():
    sensor_utils.save_email(request.form['email'])
    flash('Adres e-mail został zapisany!')
    return redirect('/get_notification_config_data')


@app.route('/save_threshold_notifications', methods=['POST'])
def save_threshold_notifications():
    data = request.form
    checkbox = False if 'contact_ok' not in request.form else True
    sensor_utils.save_threshold_notification(data)
    flash('Konfiguracja powiadomień dla progów została zapisana!')
    return redirect('/get_notification_config_data')


@socketio.on('connect')
def on_connect():
    print("Client connected")
    global active_clients
    active_clients +=1
    client_id = request.sid
    client_preferences[client_id] = {}
    if last_sensor_data:
        socketio.emit('sensor_data', last_sensor_data)
        print("Sent last available data to client:", last_sensor_data)


@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")
    global active_clients
    active_clients = active_clients-1
    client_id = request.sid
    if client_id in client_preferences:
        del client_preferences[client_id]


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        sensor_utils.initialize_sensors(sensor_objects)
    socketio.start_background_task(target=collect_sensor_data)
    socketio.start_background_task(target=emit_server_time)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
