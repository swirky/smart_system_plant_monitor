import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from simulated_sensors.simulated_light_sensor import SimulatedLightSensor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Mar123321@localhost/monitor_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins='*')
db = SQLAlchemy(app)
simulated_light_sensor = SimulatedLightSensor()

last_sensor_data = None  # Zmienna globalna do przechowywania ostatnich danych z czujnika

# Model dla danych z czujnika
class MonitorDatabase(db.Model):
    __tablename__ = 'light_sensor'
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50))
    lux = db.Column(db.Float)
    timestamp = db.Column(db.String(50))

# Funkcja do zapisywania danych w bazie
def save_sensor_data(data):
    try:
        new_data = MonitorDatabase(model=data['model'], lux=data['lux'], timestamp=data['timestamp'])
        db.session.add(new_data)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data to the database: {e}")
        
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

                # Zczytywanie danych i aktualizacja zmiennej globalnej
                data = simulated_light_sensor.read()
                last_sensor_data = data
                save_sensor_data(data)
                socketio.emit('sensor_data', last_sensor_data)  # Emitowanie danych do klientów
                print("Dane zapisane do bazy oraz wysłane do klienta:", data)
            except Exception as e:
                print(f"Error during data collection: {e}")


@app.route('/')
def index():
    return render_template('index.html')

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
    # Uruchamiamy zadanie zbierania danych przy starcie serwera
    socketio.start_background_task(target=collect_sensor_data)
    socketio.run(app, debug=False)
