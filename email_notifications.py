from flask_mail import Message
from app import mail
import logging
from datetime import datetime, timedelta
from dbmodels import db, MeasurementType, Sensor, SensorReading, ThresholdValues
import sensor_utils

logger = logging.getLogger(__name__)


def send_alert_emails_for_active_readings():
    now = datetime.now()
    thresholds = get_active_thresholds()

    for threshold, sensor_name, measurement_type_name in thresholds:
        latest_reading = get_latest_reading(threshold.sensor_id, threshold.measurement_type_id)
        if latest_reading:
            if (threshold.max_value is not None and latest_reading.value > threshold.max_value) or \
                    (threshold.min_value is not None and latest_reading.value < threshold.min_value):
                if threshold.last_notification is None or now - threshold.last_notification > timedelta(hours=1):
                    send_alert_email(sensor_name, measurement_type_name, latest_reading.value, threshold)
                    threshold.last_notification = now
                    db.session.commit()


def get_active_thresholds():
    return db.session.query(ThresholdValues, Sensor.name, MeasurementType.name).join(
        Sensor, ThresholdValues.sensor_id == Sensor.id
    ).join(
        MeasurementType, ThresholdValues.measurement_type_id == MeasurementType.id
    ).filter(ThresholdValues.notification_is_active == True).all()


def get_latest_reading(sensor_id: int, measurement_type_id: int) -> SensorReading:
    return db.session.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.measurement_type_id == measurement_type_id
    ).order_by(SensorReading.timestamp.desc()).first()


def send_alert_email(sensor_name: str, measurement_type_name: str, value: float, threshold: ThresholdValues):
    recipients = sensor_utils.get_email_recipients()
    if isinstance(recipients, str):
        recipients = [recipients]
    subject = f"ALERT: Czujnik {sensor_name} przekroczył próg!"
    body = (
        f"ALERT: Pomiar {measurement_type_name} czujnika {sensor_name}  przekroczył próg alarmowy!\n\n"
        f"Wartość: {value}\n"
        f"Minimalny próg: {threshold.min_value}\n"
        f"Maksymalny próg: {threshold.max_value}\n\n"
        f"Czas pomiaru: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Podejmij odpowiednie odpowiednie działania. Następny alert zostanie wysłany najwcześniej za godzinę."
    )
    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
        logger.info(f"Email sent to: {', '.join(recipients)}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
