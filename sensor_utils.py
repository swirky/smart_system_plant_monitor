from datetime import datetime, timedelta
import re
import logging
from sqlalchemy import func
from dbmodels import (db, SensorType, MeasurementType, SensorTypeCapabilities, Sensor, SensorReading, ThresholdValues,
                      EmailRecipients, SoilMoistureCalibration)

logger = logging.getLogger(__name__)


def commit_to_db():
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Error committing to database: {e}")
        db.session.rollback()


def sync_sensor_and_sensor_type(sensor_object) -> Sensor:
    sensor_type = SensorType.query.filter_by(name=sensor_object.type).first()
    if not sensor_type:
        sensor_type = SensorType(name=sensor_object.type)
        db.session.add(sensor_type)
        commit_to_db()
        print("Sensor type added")
    sensor = Sensor.query.filter_by(name=sensor_object.name, model=sensor_object.model).first()
    if not sensor:
        sensor = Sensor(name=sensor_object.name, model=sensor_object.model, type_id=sensor_type.id)
        db.session.add(sensor)
        commit_to_db()
        logger.info("Sensor added")
    sync_sensor_capabilities(sensor_type.id, sensor_object.measurement_types)
    return sensor


def sync_sensor_capabilities(sensor_type_id: int, measurement_types: list):
    for measurement_name in measurement_types:
        measurement_type = MeasurementType.query.filter_by(name=measurement_name).first()
        if not measurement_type:
            measurement_type = MeasurementType(name=measurement_name)
            db.session.add(measurement_type)
            commit_to_db()
        capability = SensorTypeCapabilities.query.filter_by(sensor_type_id=sensor_type_id,
                                                            measurement_type_id=measurement_type.id).first()
        if not capability:
            capability = SensorTypeCapabilities(
                sensor_type_id=sensor_type_id, measurement_type_id=measurement_type.id)
            db.session.add(capability)
            commit_to_db()


def sync_threshold_config_data(sensor_object):
    sensor = Sensor.query.filter_by(name=sensor_object.name, model=sensor_object.model).first()
    for measurement_type in sensor_object.measurement_types:
        measurement_type = MeasurementType.query.filter_by(name=measurement_type).first()
        existing_threshold_value = ThresholdValues.query.filter_by(sensor_id=sensor.id,
                                                                   measurement_type_id=measurement_type.id).first()
        if not existing_threshold_value:
            new_threshold_field = ThresholdValues(sensor_id=sensor.id, measurement_type_id=measurement_type.id,
                                                  min_value=None, max_value=None)
            db.session.add(new_threshold_field)
    commit_to_db()


def sync_soil_moisture_calibration():
    default_states = ["Bardzo Sucha", "Sucha", "Nawodniona", "Nadmiernie Nawodniona"]
    for state in default_states:
        existing_entry = SoilMoistureCalibration.query.filter_by(moisture_state=state).first()
        if not existing_entry:
            new_entry = SoilMoistureCalibration(moisture_state=state, min_value=None, max_value=None)
            db.session.add(new_entry)
    commit_to_db()


def initialize_sensors(sensor_objects: list):
    for sensor_object in sensor_objects:
        sync_sensor_and_sensor_type(sensor_object)
        sync_threshold_config_data(sensor_object)
    sync_soil_moisture_calibration()

def get_all_thresholds() -> list:
    thresholds = db.session.query(
        ThresholdValues, Sensor.name.label('sensor_name'), MeasurementType.name.label('measurement_type_name')
    ).join(Sensor, ThresholdValues.sensor_id == Sensor.id) \
        .join(MeasurementType, ThresholdValues.measurement_type_id == MeasurementType.id) \
        .all()

    return [{
        'sensor_id': t.ThresholdValues.sensor_id,
        'sensor_name': t.sensor_name,
        'measurement_type_id': t.ThresholdValues.measurement_type_id,
        'measurement_type_name': t.measurement_type_name,
        'min_value': t.ThresholdValues.min_value,
        'max_value': t.ThresholdValues.max_value,
        'notification_is_active': t.ThresholdValues.notification_is_active
    } for t in thresholds]


def get_data_from_sensors(sensor_objects: list) -> tuple:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sensor_data = {}
    for sensor_object in sensor_objects:
        data = sensor_object.read()
        if sensor_object.name not in sensor_data:
            sensor_data[sensor_object.name] = {}
        for measurement_type_name, value in data.items():
            sensor_data[sensor_object.name][measurement_type_name] = value
    return sensor_data, timestamp


def save_last_data(data: dict, timestamp: str):
    for sensor_name, measurements in data.items():
        sensor = Sensor.query.filter_by(name=sensor_name).first()
        for measurement_type_name, value in measurements.items():
            measurement_type = MeasurementType.query.filter_by(name=measurement_type_name).first()
            reading = SensorReading(sensor_id=sensor.id, measurement_type_id=measurement_type.id, value=value,
                                    timestamp=timestamp)
            db.session.add(reading)
    commit_to_db()


def save_thresholds(data: dict):
    thresholds = []
    for key, value in data.items():
        match = re.match(r"(min_value|max_value)_(\d+)_(\d+)", key)
        if match:
            field, sensor_id, measurement_type_id = match.groups()
            sensor_id = int(sensor_id)
            measurement_type_id = int(measurement_type_id)
            value = float(value) if value else None
            threshold = next((t for t in thresholds if
                              t['sensor_id'] == sensor_id and t['measurement_type_id'] == measurement_type_id), None)
            if not threshold:
                threshold = {'sensor_id': sensor_id, 'measurement_type_id': measurement_type_id, 'min_value': None,
                             'max_value': None}
                thresholds.append(threshold)
            threshold[field] = value
    for t in thresholds:
        existing = ThresholdValues.query.filter_by(sensor_id=t['sensor_id'],
                                                   measurement_type_id=t['measurement_type_id']).first()
        if existing:
            existing.min_value = t['min_value']
            existing.max_value = t['max_value']
        else:
            new_threshold = ThresholdValues(sensor_id=t['sensor_id'], measurement_type_id=t['measurement_type_id'],
                                            min_value=t['min_value'], max_value=t['max_value'])
            db.session.add(new_threshold)
    commit_to_db()


def get_email_recipients() -> str:
    email = EmailRecipients.query.first()
    return email.email if email else ''


def save_email(email: str):
    existing_email = EmailRecipients.query.first()
    if existing_email:
        existing_email.email = email
    else:
        new_email = EmailRecipients(email=email)
        db.session.add(new_email)
    commit_to_db()


def save_threshold_notification(data: dict):
    thresholds = []
    for key, value in data.items():
        if key.startswith('notification_'):
            _, sensor_id, measurement_type_id = key.split('_')
            is_active = value == 'true'
            thresholds.append({'sensor_id': int(sensor_id), 'measurement_type_id': int(measurement_type_id),
                               'notification_is_active': is_active})
    for threshold in thresholds:
        existing_threshold = ThresholdValues.query.filter_by(sensor_id=threshold['sensor_id'],
                                                             measurement_type_id=threshold[
                                                                 'measurement_type_id']).first()
        if existing_threshold:
            existing_threshold.notification_is_active = threshold['notification_is_active']
    commit_to_db()


def get_time_threshold(days: int = None, hours: int = None) -> datetime:
    if hours is not None:
        return datetime.now() - timedelta(hours=hours)
    elif days is not None:
        return datetime.now() - timedelta(days=days)


def get_sensor_measurements(sensor: Sensor, measurement_name: str, time_threshold: datetime, group_by: str) -> list:
    measurement = MeasurementType.query.filter_by(name=measurement_name).first()
    if not measurement:
        return []
    query = build_query(sensor.id, measurement.id, time_threshold, group_by)
    return query.all()


def build_query(sensor_id: int, measurement_id: int, time_threshold: datetime, group_by: str):
    return (
        db.session.query(
            func.date_trunc(group_by, SensorReading.timestamp).label('truncated_time'),
            func.avg(SensorReading.value).label('average_value')
        )
        .filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.measurement_type_id == measurement_id,
            SensorReading.timestamp >= time_threshold
        )
        .group_by(func.date_trunc(group_by, SensorReading.timestamp))
        .order_by(func.date_trunc(group_by, SensorReading.timestamp).asc())
    )


def get_measurement_with_range(sensor_objects: list, days: int = None, hours: int = None) -> dict:
    data_package = {}
    time_threshold = get_time_threshold(days, hours)
    for sensor_object in sensor_objects:
        sensor = Sensor.query.filter_by(name=sensor_object.name, model=sensor_object.model).first()
        if sensor:
            sensor_data = {}
            for measurement_name in sensor_object.measurement_types:
                group_by = 'minute' if hours == 1 else 'hour' if days in [1, 7] else 'day' if days == 30 else 'minute'
                readings = get_sensor_measurements(sensor, measurement_name, time_threshold, group_by)
                sensor_data[measurement_name] = format_readings(readings)
            data_package[sensor_object.name] = sensor_data
    return data_package


def format_readings(readings: list) -> list:
    if not readings:
        return [{"timestamp": "0000-00-00T00:00:00", "value": 0}]
    return [{"timestamp": reading.truncated_time.isoformat(), "value": reading.average_value} for reading in readings]

#------soil moisture calibration operations-----


def compare_soil_moisture(last_sensor_data):
    soil_moisture_value = last_sensor_data.get('Soil Humidity Sensor 1', {}).get('soil humidity', None)
    if soil_moisture_value is None:
        return "Unknown"
    calibration_data = SoilMoistureCalibration.query.all()
    for calibration in calibration_data:
        if calibration.min_value is not None and calibration.max_value is not None:
            if calibration.min_value <= soil_moisture_value <= calibration.max_value:
                print(calibration.moisture_state)
                return calibration.moisture_state
    return "Out of Range"


def get_soil_moisture_calibration():
    calibration_data = SoilMoistureCalibration.query.all()
    return [
        {
            'moisture_state': calibration.moisture_state,
            'min_value': calibration.min_value,
            'max_value': calibration.max_value
        }
        for calibration in calibration_data
    ]


def save_soil_moisture_calibration(calibration_data):
    states = ["bardzo_sucha", "sucha", "nawodniona", "nadmiernie_nawodniona"]
    for state in states:
        min_value = calibration_data.get(f'{state}_min')
        max_value = calibration_data.get(f'{state}_max')
        calibration = SoilMoistureCalibration.query.filter_by(moisture_state=state.replace('_', ' ').title()).first()
        if not calibration:
            calibration = SoilMoistureCalibration(moisture_state=state.replace('_', ' ').title())
        calibration.min_value = float(min_value) if min_value is not None else None
        calibration.max_value = float(max_value) if max_value is not None else None
        db.session.add(calibration)
    commit_to_db()

