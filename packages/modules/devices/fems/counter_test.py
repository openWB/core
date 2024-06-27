from unittest.mock import Mock

import requests_mock


from modules.common.component_state import CounterState
from modules.devices.fems import counter, device
from modules.devices.fems.config import Fems, FemsConfiguration, FemsCounterSetup


def test_fems_counter(monkeypatch, requests_mock: requests_mock.mock):
    # setup
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, 'get_counter_value_store', Mock(return_value=mock_counter_value_store))
    requests_mock.get('http://1.1.1.1:8084/rest/channel/(meter0|_sum)/(ActivePower.*|VoltageL.|Frequency|Grid.+' +
                      'ActiveEnergy)',
                      json=SAMPLE_RESPONSE)

    dev = device.create_device(Fems(configuration=FemsConfiguration(ip_address="1.1.1.1", password="abc")))
    dev.add_component(FemsCounterSetup())

    # execution
    dev.update()

    # evaluation
    assert mock_counter_value_store.set.call_count == 1
    assert vars(mock_counter_value_store.set.call_args[0][0]) == vars(SAMPLE_STATE)


# example FEMS response on /rest/channel/(meter0|_sum)/(ActivePower.*|VoltageL.|Frequency|Grid.+ActiveEnergy)
SAMPLE_RESPONSE = [{'accessMode': 'RO',
                    'address': 'meter0/ActivePowerL3',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': 6141},
                   {'accessMode': 'RO',
                    'address': 'meter0/ActivePower',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': 17189},
                   {'accessMode': 'RO',
                    'address': 'meter0/ActivePowerL1',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': 5575},
                   {'accessMode': 'RO',
                    'address': 'meter0/ActivePowerL2',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': 5473},
                   {'accessMode': 'RO',
                    'address': 'meter0/VoltageL1',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'mV',
                    'value': 229500},
                   {'accessMode': 'RO',
                    'address': 'meter0/VoltageL2',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'mV',
                    'value': 229300},
                   {'accessMode': 'RO',
                    'address': 'meter0/VoltageL3',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'mV',
                    'value': 229300},
                   {'accessMode': 'RO',
                    'address': 'meter0/Frequency',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'mHz',
                    'value': 50000},
                   {'accessMode': 'RO',
                    'address': '_sum/GridSellActiveEnergy',
                    'text': '',
                    'type': 'LONG',
                    'unit': 'Wh_Σ',
                    'value': 11752059},
                   {'accessMode': 'RO',
                    'address': '_sum/GridBuyActiveEnergy',
                    'text': '',
                    'type': 'LONG',
                    'unit': 'Wh_Σ',
                    'value': 1088853}]

SAMPLE_STATE = CounterState(
    currents=[24.29193899782135, 23.86829481029219, 26.78150894025294],
    exported=11752059,
    imported=1088853,
    power=17189,
    power_factors=[0.0, 0.0, 0.0],
    powers=[5575, 5473, 6141],
    voltages=[229.5, 229.3, 229.3],
)
