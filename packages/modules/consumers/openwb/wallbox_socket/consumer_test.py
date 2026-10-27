import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from control import data
from modules.consumers.openwb.wallbox_socket import consumer as wallbox_socket_consumer
from modules.consumers.openwb.wallbox_socket.config import WallboxSocket, WallboxSocketConfiguration


@pytest.mark.parametrize("tag", ["0012345678", None])
@pytest.mark.parametrize("cp_type, host, duo_num", [
    ("internal_openwb", "localhost", 0),
    ("external_openwb", "192.168.1.40", 1),
])
def test_wallbox_socket_rfid_uses_selected_reader_and_clears_only_on_request(
        tag, cp_type, host, duo_num, monkeypatch, mock_pub):
    cp_module = Mock(config=SimpleNamespace(
        type=cp_type, configuration=SimpleNamespace(ip_address=host, duo_num=duo_num)))
    data.data_init(Mock())
    monkeypatch.setattr(data.data, "cp_data", {"cp4": SimpleNamespace(chargepoint_module=cp_module)})
    rfid_topic = "openWB/internal_socket/get/rfid"

    def broker_factory(name, on_connect, on_message, **kwargs):
        assert kwargs == {"host": host, "port": 1886 if host == "localhost" else 1883}

        def receive(timeout):
            client = Mock()
            on_connect(client, None, None, 0)
            assert [call.args[0] for call in client.subscribe.call_args_list] == [
                "openWB/internal_socket/get/#"]
            topics = {"openWB/internal_socket/get/power": 100, rfid_topic: tag,
                      "openWB/internal_chargepoint/9/get/rfid": "wrong-reader"}
            for topic, value in topics.items():
                on_message(None, None, Mock(topic=topic, payload=json.dumps(value).encode()))
        return Mock(start_finite_loop=receive)

    configurable = Mock()
    monkeypatch.setattr(wallbox_socket_consumer, "BrokerClient", broker_factory)
    monkeypatch.setattr(wallbox_socket_consumer, "ConfigurableConsumer", configurable)
    publisher = Mock()
    monkeypatch.setattr(wallbox_socket_consumer, "pub_single", publisher)
    wallbox_socket_consumer.create_consumer(
        WallboxSocket(id=1, configuration=WallboxSocketConfiguration(chargepoint_id=4)))

    mock_pub.reset_mock()
    state = configurable.call_args.kwargs["update"]()

    assert state.power == 100
    assert state.rfid == tag
    publisher.assert_not_called()
    cp_module.clear_rfid.assert_not_called()

    publisher.reset_mock()
    configurable.call_args.kwargs["clear_rfid"]()

    assert [call.args for call in publisher.call_args_list] == [
        ("openWB/set/internal_socket/data/last_tag", None)]
    assert all(call.kwargs == {"hostname": host} for call in publisher.call_args_list)
