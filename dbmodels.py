from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class SensorType(db.Model):
    __tablename__ = 'sensor_types'
    id = db.Column(db.Integer, primary_key=True)
    # Typ czujnika, np. 'light_sensor'
    name = db.Column(db.String(100), nullable=False)

    sensors = db.relationship('Sensor', backref='sensor_type', lazy=True)
    def __repr__(self):
        return f"<SensorType(id={self.id}, name='{self.name}')>"


class MeasurementType(db.Model):
    __tablename__ = 'measurement_types'
    id = db.Column(db.Integer, primary_key=True)
    # Typ pomiaru, np. 'Air Temperature'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Opcjonalny opis

    def __repr__(self):
        return f"<MeasurementType(id={self.id}, name='{self.name}')>"


class SensorTypeCapabilities(db.Model):
    __tablename__ = 'sensor_type_capabilities'
    id = db.Column(db.Integer, primary_key=True)
    sensor_type_id = db.Column(db.Integer, db.ForeignKey(
        'sensor_types.id'), nullable=False)
    measurement_type_id = db.Column(db.Integer, db.ForeignKey('measurement_type.id'), nullable=False)

    def __repr__(self):
        return f"<SensorTypeCapabilities(id={self.id}, sensor_type_id={self.sensor_type_id}, measurement_type_id={self.measurement_type_id})>"


class Sensor(db.Model):
    __tablename__ = 'sensors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Nazwa czujnika
    model = db.Column(db.String(50), nullable=False)  # Model czujnika
    type_id = db.Column(db.Integer, db.ForeignKey(
        'sensor_types.id'), nullable=False)  # Klucz obcy do sensor_types
    readings = db.relationship('SensorReading', backref='sensor', lazy=True)

    def __repr__(self):
        return f"<Sensor(id={self.id}, name='{self.name}', model='{self.model}', type_id={self.type_id})>"


class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey(
        'sensors.id'), nullable=False)  # Klucz obcy do sensors
    measurement_type_id = db.Column(db.Integer, db.ForeignKey(
        'measurement_types.id'), nullable=False)  # Klucz obcy do measurement_types
    value = db.Column(db.Float, nullable=False)  # Wartość pomiaru
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now().replace(
        microsecond=0))  # Czas odczytu

    def __repr__(self):
        return f"<SensorReading(id={self.id}, sensor_id={self.sensor_id}, measurement_type_id={self.measurement_type_id}, value={self.value}, timestamp='{self.timestamp}')>"
    

class ThresholdValues(db.Model):
    __tablename__ = 'threshold_values'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    measurement_type_id = db.Column(db.Integer, db.ForeignKey('measurement_types.id'), nullable=False)
    min_value = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<ThresholdValues(sensor_id={self.sensor_id}, measurement_type_id={self.measurement_type_id}, min_value={self.min_value}, max_value={self.max_value})>"

