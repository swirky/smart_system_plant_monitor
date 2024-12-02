from datetime import datetime, timedelta
from dbmodels import db, SensorType, MeasurementType, SensorTypeCapabilities, Sensor, SensorReading
import time


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


def initialize_sensors(sensor_objects):
    for sensor_object in sensor_objects:
        add_sensor_or_sensor_type_if_not_exists(sensor_object)

def read_sensor_data(sensor_objects):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sensor_data = {}

    for sensor_object in sensor_objects:
        data = sensor_object.read()
        if sensor_object.name not in sensor_data:
            sensor_data[sensor_object.name] = {}
        for measurement_type_name, value in data.items():
            sensor_data[sensor_object.name][measurement_type_name] = value
    return sensor_data,timestamp

def save_to_database(data,timestamp):
    for sensor_name, measurements in data.items():
        sensor = Sensor.query.filter_by(name=sensor_name).first()
        for measurement_type_name, value in measurements.items():
            measurement_type = MeasurementType.query.filter_by(name=measurement_type_name).first()
            
            reading = SensorReading(
                sensor_id=sensor.id,
                measurement_type_id=measurement_type.id,
                value=value,
                timestamp=timestamp
            )
            db.session.add(reading)
    db.session.commit()