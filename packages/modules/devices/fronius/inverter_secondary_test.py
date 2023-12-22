from unittest.mock import Mock


from modules.common.store._api import LoggingValueStore
from modules.devices.fronius.config import FroniusSecondaryInverterConfiguration, FroniusSecondaryInverterSetup
from modules.devices.fronius.inverter_secondary import FroniusSecondaryInverter


def test_update(monkeypatch, mock_simcount):
    wr = FroniusSecondaryInverter(0, FroniusSecondaryInverterSetup(FroniusSecondaryInverterConfiguration(id=1)))

    mock = Mock(return_value=None)
    monkeypatch.setattr(LoggingValueStore, "set", mock)
    mock_simcount.return_value = 0, 0

    wr.update(json_wr1)

    # mock.assert_called_once()
    inverter_state = mock.call_args[0][0]
    assert inverter_state.exported == 0
    assert inverter_state.currents == [0, 0, 0]
    assert inverter_state.power == -4470.0


json_wr1 = {
    "Body": {
        "Data": {
            "Inverters": {
                "1": {
                    "Battery_Mode": "normal",
                    "DT": 1,
                    "E_Day": None,
                    "E_Total": 148955.258055555,
                    "E_Year": None,
                    "P": 20.819091796875,
                    "SOC": 95.299999999999997
                }
            },
            "SecondaryMeters": {
                "1": {
                    "Category": "METER_CAT_WR",
                    "Label": "PV- 1",
                    "MLoc": 3.0,
                    "P": 4470.0
                }
            },
            "Site": {
                "BackupMode": False,
                "BatteryStandby": False,
                "E_Day": None,
                "E_Total": 148955.258055555,
                "E_Year": None,
                "Meter_Location": "grid",
                "Mode": "bidirectional",
                "P_Akku": -11.142402648926,
                "P_Grid": -2631.999999999,
                "P_Load": -3933.5058593751,
                "P_PV": 2173.672851562,
                "rel_Autonomy": 100.0,
                "rel_SelfConsumption": 59.4570229924
            },
            "Smartloads": {
                "Ohmpilots": {}
            },
            "Version": "12"
        }
    },
    "Head": {
        "RequestArguments": {},
        "Status": {
            "Code": 0,
            "Reason": "",
            "UserMessage": ""
        },
        "Timestamp": "2023-09-25Txx:xx:xx+00:00"
    }
}

json_wr2 = {
    "Body": {
        "Data": {
            "Inverters": {
                "1": {
                    "DT": 232,
                    "E_Day": 172.69999694824219,
                    "E_Total": 3372.76953125,
                    "E_Year": 10754989,
                    "P": 108
                }
            },
            "Site": {
                "E_Day": 172.69999694824219,
                "E_Total": 3372.7694444444446,
                "E_Year": 10754989,
                "Meter_Location": "unknown",
                "Mode": "produce-only",
                "P_Akku": None,
                "P_Grid": None,
                "P_Load": None,
                "P_PV": 108,
                "rel_Autonomy": None,
                "rel_SelfConsumption": None
            },
            "Version": "12"
        }
    },
    "Head": {
        "RequestArguments": {},
        "Status": {
            "Code": 0,
            "Reason": "",
            "UserMessage": ""
        },
        "Timestamp": "2021-12-30T10:37:02+01:00"
    }
}
