from unittest.mock import Mock

import pytest

from control.ev import Ev
from helpermodules import timecheck


@pytest.mark.parametrize(
    "check_timestamp, charge_state, soc_timestamp, expected_request_soc",
    [pytest.param(False, False, "", True, id="no soc_timestamp"),
     pytest.param(True, False, "2022/05/16, 8:30:52", False, id="not charging, not expired"),
     pytest.param(False, False, "2022/05/15, 20:30:52", True, id="not charging, expired"),
     pytest.param(True, True, "2022/05/16, 8:36:52", False, id="charging, not expired"),
     pytest.param(False, True, "2022/05/16, 8:35:50", True, id="charging, expired"),
     ])
def test_soc_interval_expired(check_timestamp: bool,
                              charge_state: bool,
                              soc_timestamp: str,
                              expected_request_soc: bool,
                              monkeypatch):
    # setup
    ev = Ev(0)
    ev.data.get.soc_timestamp = soc_timestamp
    check_timestamp_mock = Mock(return_value=check_timestamp)
    monkeypatch.setattr(timecheck, "check_timestamp", check_timestamp_mock)

    # execution
    request_soc = ev.soc_interval_expired(charge_state)

    # evaluation
    assert request_soc == expected_request_soc
