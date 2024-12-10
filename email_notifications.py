from flask_mail import Message
from app import mail
from datetime import datetime, timedelta
from dbmodels import db, SensorType, MeasurementType, SensorTypeCapabilities, Sensor, SensorReading, ThresholdValues, EmailRecipients
import sensor_utils

def send_alert_emails_for_active_readings():
    now = datetime.now()

    # Pobierz wszystkie progi alarmowe z aktywnymi powiadomieniami
    thresholds = db.session.query(ThresholdValues, Sensor.name, MeasurementType.name).join(
        Sensor, ThresholdValues.sensor_id == Sensor.id
    ).join(
        MeasurementType, ThresholdValues.measurement_type_id == MeasurementType.id
    ).filter(ThresholdValues.notification_is_active == True).all()

    for threshold, sensor_name, measurement_type_name in thresholds:
        # Pobierz ostatni odczyt dla czujnika i typu pomiaru
        latest_reading = db.session.query(SensorReading).filter(
            SensorReading.sensor_id == threshold.sensor_id,
            SensorReading.measurement_type_id == threshold.measurement_type_id
        ).order_by(SensorReading.timestamp.desc()).first()

        if latest_reading:
            # Sprawdź, czy wartość przekracza próg
            if (threshold.max_value is not None and latest_reading.value > threshold.max_value) or \
               (threshold.min_value is not None and latest_reading.value < threshold.min_value):

                # Sprawdź, czy ostatni e-mail został wysłany ponad godzinę temu
                if threshold.last_notification is None or now - threshold.last_notification > timedelta(hours=1):
                    # Wyślij wiadomość e-mail
                    send_alert_email(sensor_name, measurement_type_name, latest_reading.value, threshold)

                    # Zaktualizuj czas ostatniego powiadomienia
                    threshold.last_notification = now
                    db.session.commit()


def send_alert_email(sensor_name, measurement_type_name, value, threshold):

    recipients = sensor_utils.get_email_recipients()
    if isinstance(recipients, str):  
        recipients = [recipients]

    subject = f"ALERT: Czujnik {sensor_name} przekroczył próg!"
    body = (
        f"ALERT: Czujnik {sensor_name} ({measurement_type_name}) przekroczył próg alarmowy!\n\n"
        f"Wartość: {value}\n"
        f"Minimalny próg: {threshold.min_value}\n"
        f"Maksymalny próg: {threshold.max_value}\n\n"
        f"Czas pomiaru: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Proszę podjąć odpowiednie działania."
    )

    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
        print(f"E-mail został wysłany do: {', '.join(recipients)}")
    except Exception as e:
        print(f"Błąd podczas wysyłania e-maila: {e}")
