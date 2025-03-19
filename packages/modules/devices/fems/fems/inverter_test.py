from unittest.mock import Mock

import requests_mock


from modules.common.component_state import InverterState
from modules.devices.fems.fems import inverter, device
from modules.devices.fems.fems.config import Fems, FemsConfiguration, FemsInverterSetup


def test_fems_inverter(monkeypatch, requests_mock: requests_mock.mock):
    # setup
    mock_inverter_value_store = Mock()
    monkeypatch.setattr(inverter, 'get_inverter_value_store', Mock(return_value=mock_inverter_value_store))
    requests_mock.get('http://1.1.1.1:8084/rest/channel/_sum/(ProductionActivePower|ProductionActiveEnergy)',
                      json=SAMPLE_RESPONSE)

    dev = device.create_device(Fems(configuration=FemsConfiguration(ip_address="1.1.1.1", password="abc")))
    dev.add_component(FemsInverterSetup())

    # execution
    dev.update()

    # evaluation
    assert mock_inverter_value_store.set.call_count == 1
    assert vars(mock_inverter_value_store.set.call_args[0][0]) == vars(SAMPLE_STATE)


# example FEMS response on /rest/channel/_sum/(ProductionActivePower|ProductionActiveEnergy)
SAMPLE_RESPONSE = [{'accessMode': 'RO',
                    'address': '_sum/ProductionActiveEnergy',
                    'text': '',
                    'type': 'LONG',
                    'unit': 'Wh_Σ',
                    'value': 18988374},
                   {'accessMode': 'RO',
                    'address': '_sum/ProductionActivePower',
                    'text': 'Total production; always positive',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': -9}]

SAMPLE_STATE = InverterState(
    currents=[0.0, 0.0, 0.0],
    dc_power=None,
    exported=18988374,
    power=9
)
