import json
from unittest.mock import Mock, call

import pytest

from modules.consumers.generic.mqtt import consumer as mqtt_consumer
from modules.consumers.generic.mqtt.config import Mqtt


@pytest.mark.parametrize("tag", ["0012345678", None])
@pytest.mark.parametrize("timestamp", [None, 1652683200, 0])
def test_mqtt_rfid_is_returned_and_only_cleared_on_request(tag, timestamp, monkeypatch, mock_pub):
    def broker_factory(name, on_connect, on_message):
        def receive():
            values = {"power": 100, "imported": 20, "exported": 0, "rfid": tag}
            if timestamp is not None:
                values["rfid_timestamp"] = timestamp
            for key, value in values.items():
                on_message(None, None, Mock(topic=f"openWB/mqtt/consumer/1/get/{key}",
                                            payload=json.dumps(value).encode()))
        return Mock(start_finite_loop=receive)

    configurable = Mock()
    monkeypatch.setattr(mqtt_consumer, "BrokerClient", broker_factory)
    monkeypatch.setattr(mqtt_consumer, "ConfigurableConsumer", configurable)
    mqtt_consumer.create_consumer(Mqtt(id=1))

    state = configurable.call_args.kwargs["update"]()

    assert state.power == 100
    assert state.rfid == tag
    assert state.rfid_timestamp == (timestamp if tag else None)
    mock_pub.pub.assert_not_called()

    mock_pub.pub.reset_mock()
    configurable.call_args.kwargs["clear_rfid"]()
    assert mock_pub.pub.call_args_list == [call("openWB/mqtt/consumer/1/get/rfid", None),
                                           call("openWB/mqtt/consumer/1/get/rfid_timestamp", None)]
