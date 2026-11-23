from unittest.mock import Mock

import pytest

from helpermodules.setdata import SetData


@pytest.mark.parametrize("payload, valid", [
    pytest.param(b"6000", True, id="number"),
    pytest.param(b"0", True, id="zero disables the check"),
    pytest.param(b'"6000"', False, id="string"),
    pytest.param(b"-1", False, id="negative"),
])
def test_process_bat_topic_config_max_power_is_validated(payload, valid, mock_pub):
    setdata = SetData.__new__(SetData)
    msg = Mock(topic="openWB/set/bat/4/config/max_power", payload=payload)

    setdata.process_bat_topic(msg)

    published = [call.args[0] for call in mock_pub.pub.call_args_list if call.args[1] != ""]
    assert (published == ["openWB/bat/4/config/max_power"]) is valid
