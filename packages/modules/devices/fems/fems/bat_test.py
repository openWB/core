from unittest.mock import Mock

import requests_mock


from modules.common.component_state import BatState
from modules.devices.fems.fems import bat, device
from modules.devices.fems.fems.config import Fems, FemsConfiguration, FemsBatSetup


def test_fems_bat(monkeypatch, requests_mock: requests_mock.mock):
    # setup
    mock_bat_value_store = Mock()
    monkeypatch.setattr(bat, 'get_bat_value_store', Mock(return_value=mock_bat_value_store))
    requests_mock.get('http://1.1.1.1:8084/rest/channel/(ess0|_sum)/(Soc|DcChargeEnergy|DcDischargeEnergy|'
                      + 'GridActivePower|ProductionActivePower|ConsumptionActivePower)',
                      json=SAMPLE_RESPONSE)

    dev = device.create_device(Fems(configuration=FemsConfiguration(ip_address="1.1.1.1", password="abc")))
    dev.add_component(FemsBatSetup())

    # execution
    dev.update()

    # evaluation
    assert mock_bat_value_store.set.call_count == 1
    assert vars(mock_bat_value_store.set.call_args[0][0]) == vars(SAMPLE_STATE)


# example FEMS response on "http://" + self.ip_address + ":8084/rest/channel/(ess0|_sum)/" +
#    "(Soc|DcChargeEnergy|DcDischargeEnergy|GridActivePower|ProductionActivePower|ConsumptionActivePower)"
SAMPLE_RESPONSE = [{'accessMode': 'RO',
                    'address': '_sum/ConsumptionActivePower',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': 17183},
                   {'accessMode': 'RO',
                    'address': '_sum/ProductionActivePower',
                    'text': 'Total production; always positive',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': -9},
                   {'accessMode': 'RO',
                    'address': '_sum/GridActivePower',
                    'text': 'Grid exchange power. Negative values for sell-to-grid; positive for '
                    'buy-from-grid',
                    'type': 'INTEGER',
                    'unit': 'W',
                    'value': 17164},
                   {'accessMode': 'RO',
                    'address': 'ess0/Soc',
                    'text': '',
                    'type': 'INTEGER',
                    'unit': '%',
                    'value': 6},
                   {'accessMode': 'RO',
                    'address': 'ess0/DcChargeEnergy',
                    'text': '',
                    'type': 'LONG',
                    'unit': 'Wh_Σ',
                    'value': 3013394},
                   {'accessMode': 'RO',
                    'address': 'ess0/DcDischargeEnergy',
                    'text': '',
                    'type': 'LONG',
                    'unit': 'Wh_Σ',
                    'value': 3202108}]

SAMPLE_STATE = BatState(
    exported=3202108,
    imported=3013394,
    power=-28,
    soc=6
)
