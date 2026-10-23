import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from helpermodules import setdata
from helpermodules.subdata import SubData
from modules.internal_chargepoint_handler.internal_socket_config import InternalSocket


@pytest.mark.parametrize("suffix, value", [
    ("data/set_state", True), ("data/detected", True),
    ("data/last_tag", "0012345678"), ("data/last_tag", None),
    ("get/state", False), ("get/fault_state", 2), ("get/fault_str", "Messfehler"),
    ("get/power", 500.0), ("get/imported", 1000.0), ("get/exported", 0.0),
    ("get/currents", [2.2, 0, 0]), ("get/voltages", [230, 0, 0]),
    ("get/powers", [500, 0, 0]),
    ("get/error_timestamp", None),
    ("get/rfid", "0012345678"), ("get/rfid", None),
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


def test_handler_loop_uses_socket_data_updated_by_mqtt(monkeypatch):
    from unittest.mock import MagicMock
    from modules.chargepoints.internal_openwb.config import InternalChargepointMode
    from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler_module
    from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
        GlobalHandlerData, InternalChargepoint, RfidData)

    monkeypatch.setattr(SubData, "internal_socket_data", InternalSocket())
    subscriber = SubData.__new__(SubData)
    subscriber.process_internal_socket_topic(SimpleNamespace(
        topic="openWB/internal_socket/data/set_state", payload=json.dumps(True).encode()))
    monkeypatch.setattr(SubData, "internal_chargepoint_data", {
        "global_data": GlobalHandlerData(heartbeat=1000), "cp0": InternalChargepoint(),
        "rfid_data": RfidData(last_tag="0012345678")})
    monkeypatch.setattr(SubData, "system_data", {
        "system": SimpleNamespace(data={"debug_level": 10})})
    monkeypatch.setattr(handler_module.time, "sleep", Mock())
    monkeypatch.setattr(handler_module, "clear_in_memory_log_handler", Mock())
    handler = handler_module.InternalChargepointHandler.__new__(handler_module.InternalChargepointHandler)
    handler.cp0 = Mock(mode=InternalChargepointMode.SERIES)
    handler.cp1 = None
    handler.socket = Mock()
    handler.cp0_client_handler = SimpleNamespace(client=MagicMock())
    handler.cp1_client_handler = None
    from modules.common.fault_state import ComponentInfo, FaultState
    handler.fault_state_info_cp0 = FaultState(ComponentInfo(0, "Test", "internal_chargepoint"))
    handler.event_stop = Mock(is_set=Mock(side_effect=[False, True]))

    handler.loop()

    handler.socket.update.assert_called_once()
    global_data, socket_data = handler.socket.update.call_args.args
    assert global_data.heartbeat == 1000
    assert socket_data.set_state is True
    assert socket_data.last_tag is None


@pytest.mark.parametrize("heartbeat, expected_on", [(1000, True), (900, False)])
def test_socket_handler_uses_shared_chargepoint_heartbeat(heartbeat, expected_on, monkeypatch):
    from modules.common.fault_state import ComponentInfo, FaultState
    from modules.internal_chargepoint_handler import internal_chargepoint_handler as handler_module
    from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import GlobalHandlerData
    from modules.internal_chargepoint_handler.internal_socket_config import InternalSocketData

    monkeypatch.setattr(handler_module.timecheck, "create_timestamp", Mock(return_value=1000))
    handler = handler_module.HandlerInternalSocket.__new__(handler_module.HandlerInternalSocket)
    handler.module = Mock(fault_state=FaultState(ComponentInfo(None, "Test", "internal_socket")))
    handler.update_state = handler_module.UpdateInternalSocketState(handler.module)

    assert handler.update(GlobalHandlerData(heartbeat=heartbeat), InternalSocketData(set_state=True))

    handler.module.set_state.assert_called_once_with(expected_on)
    chargepoint = handler_module.HandlerChargepoint.__new__(handler_module.HandlerChargepoint)
    assert chargepoint._check_heartbeat_expired(heartbeat) is not expected_on


@pytest.mark.parametrize("first_ack", ["chargepoint", "consumer"])
def test_rfid_scan_is_independent_of_acknowledgement_order(first_ack, monkeypatch):
    import asyncio
    from modules.internal_chargepoint_handler import rfid
    from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import RfidData
    from modules.consumers.openwb.internal_socket import consumer as socket_consumer
    from modules.consumers.openwb.internal_socket.config import InternalSocket as SocketConsumer

    monkeypatch.setattr(SubData, "internal_socket_data", InternalSocket())
    source = {"rfid_data": RfidData()}
    monkeypatch.setattr(SubData, "internal_chargepoint_data", source)
    setter = setdata.SetData.__new__(setdata.SetData)
    subscriber = SubData.__new__(SubData)

    def message(topic, value):
        return SimpleNamespace(topic=topic, payload=json.dumps(value).encode())

    def publish(topic, value, **kwargs):
        if value == "":
            return
        if topic.startswith("openWB/set/internal_socket/"):
            setter.process_internal_socket_topic(message(topic, value))
        elif topic == "openWB/set/internal_chargepoint/last_tag":
            setter.process_internal_chargepoint_topic(message(topic, value))
        elif topic.startswith("openWB/internal_socket/"):
            subscriber.process_internal_socket_topic(message(topic, value))
        elif topic == "openWB/internal_chargepoint/last_tag":
            subscriber.process_internal_chargepoint_topic(None, source, message(topic, value))

    monkeypatch.setattr(setdata, "Pub", Mock(return_value=Mock(pub=publish)))
    monkeypatch.setattr(rfid, "Pub", Mock(return_value=Mock(pub=publish)))
    monkeypatch.setattr(rfid, "categorize", lambda event: event)
    monkeypatch.setattr(socket_consumer, "pub_single", publish)
    configurable = Mock()
    monkeypatch.setattr(socket_consumer, "ConfigurableConsumer", configurable)
    socket_consumer.create_consumer(SocketConsumer(id=1))

    async def keyboard_events():
        for digit in "0012345678":
            yield SimpleNamespace(type=rfid.ecodes.EV_KEY, keystate=1,
                                  scancode=getattr(rfid.ecodes, f"KEY_{digit}"))
        yield SimpleNamespace(type=rfid.ecodes.EV_KEY, keystate=1, scancode=rfid.ecodes.KEY_ENTER)

    def scan():
        reader = rfid.RfidReader.__new__(rfid.RfidReader)
        device = SimpleNamespace(path="/test/rfid", async_read_loop=keyboard_events)
        asyncio.run(reader._read_events(device))

    def acknowledge_chargepoint():
        setter.process_internal_chargepoint_topic(message("openWB/set/internal_chargepoint/last_tag", None))

    acknowledge_consumer = configurable.call_args.kwargs["clear_rfid"]
    scan()
    assert source["rfid_data"].last_tag == "0012345678"
    assert SubData.internal_socket_data.data.last_tag == "0012345678"

    if first_ack == "chargepoint":
        acknowledge_chargepoint()
        assert SubData.internal_socket_data.data.last_tag == "0012345678"
        acknowledge_consumer()
    else:
        acknowledge_consumer()
        assert source["rfid_data"].last_tag == "0012345678"
        acknowledge_chargepoint()

    assert source["rfid_data"].last_tag is None
    assert SubData.internal_socket_data.data.last_tag is None
    scan()
    assert source["rfid_data"].last_tag == "0012345678"
    assert SubData.internal_socket_data.data.last_tag == "0012345678"


@pytest.mark.parametrize("tag", ["0012345678", None])
def test_setdata_does_not_distribute_chargepoint_tags(tag, monkeypatch):
    publisher = Mock()
    monkeypatch.setattr(setdata, "Pub", Mock(return_value=publisher))
    setter = setdata.SetData.__new__(setdata.SetData)

    setter.process_internal_chargepoint_topic(SimpleNamespace(
        topic="openWB/set/internal_chargepoint/last_tag", payload=json.dumps(tag).encode()))

    publisher.pub.assert_any_call("openWB/internal_chargepoint/last_tag", tag, retain=True)
    assert all("internal_socket" not in call.args[0] for call in publisher.pub.call_args_list)
