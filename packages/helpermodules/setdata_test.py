from unittest.mock import Mock

import pytest

from helpermodules.setdata import SetData


@pytest.mark.parametrize("payload, expected", [
    (b"true", True),
    (b"false", False),
    (b"null", None),
    (b'"true"', None),
    (b"{}", None),
    (b"2", None),
])
def test_process_system_topic_update_feedback(payload, expected, mock_pub):
    setdata = SetData.__new__(SetData)
    topic = "openWB/set/system/update_feedback"
    msg = Mock(topic=topic, payload=payload)

    setdata.process_system_topic(msg)

    if expected is None:
        mock_pub.pub.assert_called_once_with(topic, "")
    else:
        assert mock_pub.pub.call_count == 2
        mock_pub.pub.assert_any_call("openWB/system/update_feedback", expected, retain=True)
        mock_pub.pub.assert_any_call(topic, "")


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
