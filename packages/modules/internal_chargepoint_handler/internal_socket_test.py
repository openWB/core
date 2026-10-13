import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from helpermodules import setdata
from helpermodules.subdata import SubData
from modules.internal_chargepoint_handler.internal_socket_config import InternalSocket


@pytest.mark.parametrize("suffix, value", [
    ("data/set_state", True), ("data/heartbeat", 1234567890.0),
    ("get/state", False), ("get/fault_state", 2), ("get/fault_str", "Messfehler"),
    ("get/power", 500.0), ("get/imported", 1000.0), ("get/exported", 0.0),
    ("get/currents", [2.2, 0, 0]), ("get/voltages", [230, 0, 0]),
    ("get/powers", [500, 0, 0]), ("get/timestamp", 1234567890.0),
    ("get/error_timestamp", None),
])
def test_internal_socket_set_topics_are_validated_and_stored(suffix, value, monkeypatch):
    publisher = Mock()
    monkeypatch.setattr(setdata, "Pub", Mock(return_value=publisher))
    monkeypatch.setattr(SubData, "internal_socket_data", InternalSocket())
    setter = setdata.SetData.__new__(setdata.SetData)
    setter.process_internal_socket_topic(SimpleNamespace(
        topic=f"openWB/set/internal_socket/{suffix}", payload=json.dumps(value).encode()))
    publisher.pub.assert_any_call(f"openWB/internal_socket/{suffix}", value, retain=True)
    subscriber = SubData.__new__(SubData)
    subscriber.process_internal_socket_topic(SimpleNamespace(
        topic=f"openWB/internal_socket/{suffix}", payload=json.dumps(value).encode()))
    branch, key = suffix.split("/")
    assert getattr(getattr(SubData.internal_socket_data, branch), key) == value
