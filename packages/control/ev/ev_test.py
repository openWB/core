from typing import Optional
from unittest.mock import Mock

import pytest

from control.ev.ev import Ev
from helpermodules import timecheck
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.mqtt.config import MqttSocSetup
from modules.vehicles.mqtt.soc import create_vehicle


@pytest.mark.parametrize(
    "check_timestamp, charge_state, soc_request_timestamp, expected_request_soc",
    [pytest.param(False, False, None, True, id="no soc_request_timestamp"),
     pytest.param(True, False, 100, False, id="not charging, not expired"),
     pytest.param(False, False, 100, True, id="not charging, expired"),
     pytest.param(True, True, 100, False, id="charging, not expired"),
     pytest.param(False, True, 100, True, id="charging, expired"),
     ])
def test_soc_interval_expired(check_timestamp: bool,
                              charge_state: bool,
                              soc_request_timestamp: Optional[float],
                              expected_request_soc: bool,
                              monkeypatch):
    # setup
    ev = Ev(0)
    ev.soc_module = create_vehicle(MqttSocSetup(), 0)
    ev.data.get.soc_request_timestamp = soc_request_timestamp
    check_timestamp_mock = Mock(return_value=check_timestamp)
    monkeypatch.setattr(timecheck, "check_timestamp", check_timestamp_mock)

    # execution
    request_soc = ev.soc_interval_expired(VehicleUpdateData(charge_state=charge_state))

    # evaluation
    assert request_soc == expected_request_soc
