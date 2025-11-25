import unittest
from unittest.mock import patch, MagicMock
from modules.vehicles.homeassistant.soc import fetch_soc, HaVehicleSocSetup, HaVehicleSocConfiguration


class TestSoc(unittest.TestCase):

    def setUp(self):
        self.test_cases = [{
            "sample_data": {
                "entity_id": "sensor.ioniq_ev_battery_level",
                "state": "84",
                "attributes": {
                    "state_class": "measurement",
                    "unit_of_measurement": "%",
                    "device_class": "battery",
                    "friendly_name": "IONIQ EV Battery Level"
                },
                "last_changed": "2025-09-29T17:48:02.754865+00:00",
                "last_reported": "2025-09-29T17:48:02.754865+00:00",
                "last_updated": "2025-09-29T17:48:02.754865+00:00",
                "context": {
                    "id": "05K6B4GTT29YSKIDVJV2R7V8KY",
                    "parent_id": None,
                    "user_id": None
                }
            },
            "url": "http://1.1.1.1:4711",
            "entity_id": "sensor.ioniq_ev_battery_level",
            "token": "testtoken",
            "expected_soc": 84,
            "expected_range": None,
            "expected_timestamp": 1759168082
        }]

    @patch('soc.req.get_http_session')
    def test_fetch_soc(self, mock_get_http_session):
        for case in self.test_cases:
            mock_response = MagicMock()
            mock_response.json.return_value = case['sample_data']
            mock_get_http_session.return_value.get.return_value = mock_response

            vehicle_config = HaVehicleSocSetup(configuration=HaVehicleSocConfiguration(
                url=case['url'],
                token=case['token'],
                entity_id=case['entity_id']
            ))
            car_state = fetch_soc(vehicle_config)

            self.assertEqual(car_state.soc, case['expected_soc'])
            self.assertEqual(car_state.range, case['expected_range'])
            self.assertEqual(car_state.soc_timestamp, case['expected_timestamp'])
