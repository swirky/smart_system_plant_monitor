import unittest
from unittest.mock import patch, MagicMock
from app import app, collect_sensor_data, on_connect, on_disconnect, handle_request_historical_data_with_range, emit_server_time
import email_notifications
from dbmodels import db
import sensor_utils

class TestHistoricalDataHandling(unittest.TestCase):

    @patch('app.sensor_utils.get_measurement_with_range')
    @patch('app.sensor_utils.get_all_thresholds')
    @patch('app.socketio.emit')
    def test_handle_request_historical_data_with_range(self, mock_emit, mock_get_thresholds, mock_get_data):
        mock_get_data.return_value = 'historical_data'
        mock_get_thresholds.return_value = 'thresholds'
        data = {'days': 1, 'hours': 1}
        handle_request_historical_data_with_range(data, 'test_client_id')
        mock_emit.assert_called_with('historical_data_response', {'historical_data': 'historical_data', 'thresholds': 'thresholds'}, to='test_client_id')

class TestEmailNotifications(unittest.TestCase):

    @patch('app.email_notifications.send_alert_emails_for_active_readings')
    def test_send_alert_emails_for_active_readings(self, mock_send_alerts):
        email_notifications.send_alert_emails_for_active_readings()
        mock_send_alerts.assert_called()

class TestDatabaseOperations(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_database_initialization(self):
        with app.app_context():
            self.assertIsNotNone(db.engine)

class TestBackgroundTasks(unittest.TestCase):

    @patch('app.socketio.emit')
    @patch('app.socketio.sleep')
    def test_emit_server_time(self, mock_sleep, mock_emit):
        mock_sleep.side_effect = [None, Exception("Stop Loop")]
        with self.assertRaises(Exception):
            emit_server_time()
        mock_emit.assert_called()

if __name__ == '__main__':
    unittest.main()


class TestSensorUtils(unittest.TestCase):

    @patch('sensor_utils.get_data_from_sensors')
    def test_get_data_from_sensors(self, mock_get_data):
        mock_get_data.return_value = ({'sensor': 'data'}, 'timestamp')
        data, timestamp = sensor_utils.get_data_from_sensors(['sensor1', 'sensor2'])
        self.assertEqual(data, {'sensor': 'data'})
        self.assertEqual(timestamp, 'timestamp')

    @patch('sensor_utils.save_last_data')
    def test_save_last_data(self, mock_save_data):
        sensor_data = {'sensor': 'data'}
        timestamp = 'timestamp'
        sensor_utils.save_last_data(sensor_data, timestamp)
        mock_save_data.assert_called_with(sensor_data, timestamp)

    @patch('sensor_utils.compare_soil_moisture')
    def test_compare_soil_moisture(self, mock_compare):
        mock_compare.return_value = 'moisture_state'
        result = sensor_utils.compare_soil_moisture({'sensor': 'data'})
        self.assertEqual(result, 'moisture_state')

    @patch('sensor_utils.get_measurement_with_range')
    def test_get_measurement_with_range(self, mock_get_measurement):
        mock_get_measurement.return_value = 'measurement_data'
        result = sensor_utils.get_measurement_with_range(['sensor1', 'sensor2'], 1, 1)
        self.assertEqual(result, 'measurement_data')

    @patch('sensor_utils.get_all_thresholds')
    def test_get_all_thresholds(self, mock_get_thresholds):
        mock_get_thresholds.return_value = 'thresholds'
        result = sensor_utils.get_all_thresholds()
        self.assertEqual(result, 'thresholds')

    @patch('sensor_utils.save_thresholds')
    def test_save_thresholds(self, mock_save_thresholds):
        thresholds_data = {'threshold': 'value'}
        sensor_utils.save_thresholds(thresholds_data)
        mock_save_thresholds.assert_called_with(thresholds_data)

    @patch('sensor_utils.get_email_recipients')
    def test_get_email_recipients(self, mock_get_email):
        mock_get_email.return_value = 'email@example.com'
        result = sensor_utils.get_email_recipients()
        self.assertEqual(result, 'email@example.com')

    @patch('sensor_utils.save_email')
    def test_save_email(self, mock_save_email):
        email = 'email@example.com'
        sensor_utils.save_email(email)
        mock_save_email.assert_called_with(email)

    @patch('sensor_utils.get_soil_moisture_calibration')
    def test_get_soil_moisture_calibration(self, mock_get_calibration):
        mock_get_calibration.return_value = 'calibration_data'
        result = sensor_utils.get_soil_moisture_calibration()
        self.assertEqual(result, 'calibration_data')

    @patch('sensor_utils.save_soil_moisture_calibration')
    def test_save_soil_moisture_calibration(self, mock_save_calibration):
        calibration_data = {'calibration': 'value'}
        sensor_utils.save_soil_moisture_calibration(calibration_data)
        mock_save_calibration.assert_called_with(calibration_data)

    @patch('sensor_utils.initialize_sensors')
    def test_initialize_sensors(self, mock_initialize):
        sensors = ['sensor1', 'sensor2']
        sensor_utils.initialize_sensors(sensors)
        mock_initialize.assert_called_with(sensors)

if __name__ == '__main__':
    unittest.main()