import unittest
from unittest.mock import patch, MagicMock
from soc import fetch_soc, JsonSocSetup, JsonSocConfiguration


class TestSoc(unittest.TestCase):

    def setUp(self):
        self.test_cases = [
            {
                'sample_data': {
                    'energy': [{
                        'updated_at': '2025-01-04 10:00:13+00:00',
                        'autonomy': 214.0,
                        'battery': None,
                        'charging': {
                            'charging_mode': 'No',
                            'charging_rate': 0,
                            'next_delayed_time': 'PT9H1M',
                            'plugged': True,
                            'remaining_time': 'PT0S',
                            'status': 'Disconnected'
                        },
                        'consumption': None,
                        'level': 69.0,
                        'residual': None,
                        'type': 'Electric'
                    }]
                },
                'url': "http://example.com/soc1",
                'soc_pattern': '.energy[0].level',
                'range_pattern': '.energy[0].autonomy',
                'timestamp_pattern': '.energy[0].updated_at',
                'expected_soc': 69,
                'expected_range': 214,
                'expected_timestamp': 1735984813
            },
            {
                'sample_data': {
                    "response": {
                        "value": "20.2",
                        "timestamp": 1736108141
                    }
                },
                'url': "http://example.com/soc2",
                'soc_pattern': '.response.value',
                'range_pattern': None,
                'timestamp_pattern': '.response.timestamp',
                'expected_soc': 20.2,
                'expected_range': None,
                'expected_timestamp': 1736108141
            }
        ]

    @patch('soc.req.get_http_session')
    def test_fetch_soc(self, mock_get_http_session):
        for case in self.test_cases:
            mock_response = MagicMock()
            mock_response.json.return_value = case['sample_data']
            mock_get_http_session.return_value.get.return_value = mock_response

            vehicle_config = JsonSocSetup(configuration=JsonSocConfiguration(
                url=case['url'],
                soc_pattern=case['soc_pattern'],
                range_pattern=case['range_pattern'],
                timestamp_pattern=case['timestamp_pattern']
            ))
            car_state = fetch_soc(vehicle_config)

            self.assertEqual(car_state.soc, case['expected_soc'])
            self.assertEqual(car_state.range, case['expected_range'])
            self.assertEqual(car_state.soc_timestamp, case['expected_timestamp'])
