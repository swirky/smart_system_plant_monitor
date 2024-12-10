from datetime import datetime, timedelta
import re
from sqlalchemy import func
from dbmodels import db, SensorType, MeasurementType, SensorTypeCapabilities, Sensor, SensorReading, ThresholdValues, EmailRecipients


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

def add_threshold_config_data(sensor_object):
    sensor = Sensor.query.filter_by(name=sensor_object.name, model=sensor_object.model).first()
    for measurement_type in sensor_object.measurement_types:
        measurement_type = MeasurementType.query.filter_by(name=measurement_type).first()
        existing_threshold_value = ThresholdValues.query.filter_by(sensor_id = sensor.id, measurement_type_id=measurement_type.id).first()
        if not existing_threshold_value:
            new_threshold_field = ThresholdValues(
                sensor_id = sensor.id,
                measurement_type_id = measurement_type.id,
                min_value = None,
                max_value = None
            )
            db.session.add(new_threshold_field)
    db.session.commit()  

def get_all_thresholds():
    # Pobierz wszystkie progi alarmowe wraz z nazwami czujników i typów pomiarów
    thresholds = db.session.query(
        ThresholdValues,
        Sensor.name.label('sensor_name'),
        MeasurementType.name.label('measurement_type_name')
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
        'last_notification': t.ThresholdValues.last_notification,
        'notification_is_active': t.ThresholdValues.notification_is_active
    } for t in thresholds]


def add_sensor_reading(sensor, reading_value):
    reading = SensorReading(sensor_id=sensor.id, value=reading_value)
    db.session.add(reading)
    db.session.commit()

def initialize_sensors(sensor_objects):
    for sensor_object in sensor_objects:
        add_sensor_or_sensor_type_if_not_exists(sensor_object)
        add_threshold_config_data(sensor_object)


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

def save_thresholds_to_db(data):
    thresholds = []
    for key,value in data.items():
        match = re.match(r"(min_value|max_value)_(\d+)_(\d+)", key)
        if match:
            field,sensor_id, measurement_type_id = match.groups()
            sensor_id = int(sensor_id)
            measurement_type_id =int(measurement_type_id)
            value = float(value) if value else None
            threshold = next((t for t in thresholds if t['sensor_id'] == sensor_id and t['measurement_type_id'] == measurement_type_id), None)
            if not threshold:
                threshold = {'sensor_id': sensor_id, 'measurement_type_id': measurement_type_id, 'min_value': None, 'max_value': None}
                thresholds.append(threshold)
            threshold[field] = value

    for t in thresholds:
        existing = ThresholdValues.query.filter_by(
            sensor_id=t['sensor_id'],
            measurement_type_id=t['measurement_type_id']
        ).first()
        if existing:
            existing.min_value = t['min_value']
            existing.max_value = t['max_value']
        else:
            new_threshold = ThresholdValues(
                sensor_id=t['sensor_id'],
                measurement_type_id=t['measurement_type_id'],
                min_value=t['min_value'],
                max_value=t['max_value']
            )
            db.session.add(new_threshold)
    db.session.commit()

#-------------------funkcje do zczytywania danych z bazy i zapisywania dla zakładki konfiguracji powiadomień---------

def get_email_recipients():
    email = EmailRecipients.query.first()
    return email.email if email else ''

def save_email_to_db(email):
    existing_email = EmailRecipients.query.first()
    if existing_email:
        existing_email.email = email
    else:
        new_email = EmailRecipients(email=email)
        db.session.add(new_email)      
    db.session.commit()

def save_threshold_notification_to_db(data):
    print(data.get('notification_1_1'))
    thresholds=[]
    for key, value in data.items():
        if key.startswith('notification_'):  # Filtruj dane checkboxów
            _, sensor_id, measurement_type_id = key.split('_')
            is_active = value == 'true'  # Porównaj wartość z "true"

            thresholds.append({
                'sensor_id': int(sensor_id),
                'measurement_type_id': int(measurement_type_id),
                'notification_is_active': is_active
            })

    # Aktualizacja bazy
    for threshold in thresholds:
        sensor_id = threshold.get("sensor_id")
        measurement_type_id = threshold.get("measurement_type_id")
        is_active = threshold.get("notification_is_active")

        print(f"Przetwarzanie: sensor_id={sensor_id}, measurement_type_id={measurement_type_id}, is_active={is_active}")

        existing_threshold = ThresholdValues.query.filter_by(
            sensor_id=sensor_id,
            measurement_type_id=measurement_type_id
        ).first()

        if existing_threshold:
            existing_threshold.notification_is_active = is_active

    db.session.commit()


#--------------------funkcje do zczytywania danych z bazy  do wykresów-----------------------------------------------

def get_time_threshold(days, hours):
    if hours is not None:
        return datetime.now() - timedelta(hours=hours)
    elif days is not None:
        return datetime.now() - timedelta(days=days)

def get_sensor_measurements(sensor,measurement_name, time_threshold,group_by):
    measurement = MeasurementType.query.filter_by(name=measurement_name).first()
    if not measurement:
        return []
    query = build_query(sensor.id, measurement.id, time_threshold,group_by)
    return query.all()


def build_query(sensor_id,measurement_id,time_threshold,group_by):
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


def read_measurement_from_db_within_range(sensor_objects,days=None,hours=None):
    data_package={}
    time_threshold = get_time_threshold(days,hours)
    for sensor_object in sensor_objects:
        sensor = Sensor.query.filter_by(name=sensor_object.name, model=sensor_object.model).first()
        if sensor:
            sensor_data={}
            for measurement_name in sensor_object.measurement_types:
                if hours==1:
                    group_by='minute'
                elif days in [1,7]:
                    group_by='hour'
                elif days==30:
                    group_by='day'

                readings = get_sensor_measurements(sensor, measurement_name, time_threshold,group_by)
                sensor_data[measurement_name] = format_readings(readings)
            data_package[sensor_object.name]= sensor_data
    return data_package

def format_readings(readings):
    if not readings:
        return [{"timestamp": "0000-00-00T00:00:00", "value": 0}]
    return [
        {
            "timestamp": reading.truncated_time.isoformat(),
            "value": reading.average_value
        }
        for reading in readings
    ]
        