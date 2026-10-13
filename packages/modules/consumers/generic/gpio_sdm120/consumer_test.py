import json
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from helpermodules.subdata import SubData
from modules.common import configurable_consumer, fault_state
from modules.consumers.generic.gpio_sdm120 import consumer as module
from modules.consumers.generic.gpio_sdm120.config import GpioSdm120, GpioSdm120Configuration


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(SubData, "consumer_data", {})
    cp = SimpleNamespace(type="external_openwb", configuration=SimpleNamespace(ip_address="192.168.1.40"))
    monkeypatch.setattr(SubData, "cp_data", {"cp4": SimpleNamespace(
        chargepoint=SimpleNamespace(chargepoint_module=SimpleNamespace(config=cp)))})
    topics = {"power": 500, "imported": 1234, "exported": 0, "currents": [2.2, 0, 0],
              "voltages": [230, 0, 0], "powers": [500, 0, 0], "state": False,
              "fault_state": 0, "fault_str": "Kein Fehler.", "timestamp": time.time()}
    brokers = []

    def broker_factory(name, on_connect, on_message, host, port):
        broker = Mock(host=host, port=port)

        def loop(timeout):
            on_connect(broker.client, None, {}, 0)
            for key, value in topics.items():
                on_message(broker.client, None, SimpleNamespace(
                    topic=f"openWB/internal_socket/get/{key}", payload=json.dumps(value).encode()))

        broker.start_finite_loop.side_effect = loop
        brokers.append(broker)
        return broker

    monkeypatch.setattr(module, "BrokerClient", broker_factory)
    commands = Mock()
    monkeypatch.setattr(module, "pub_single", commands)
    monkeypatch.setattr(configurable_consumer, "get_component_value_store", Mock())
    monkeypatch.setattr(configurable_consumer, "SimCounterConsumer", Mock())
    peak_filter = Mock()
    peak_filter.check_values.return_value = (1234, 0)
    monkeypatch.setattr(configurable_consumer, "PeakFilter", Mock(return_value=peak_filter))
    publisher = Mock()
    monkeypatch.setattr(fault_state, "Pub", Mock(return_value=publisher))
    return topics, brokers, commands, publisher, cp


@pytest.mark.parametrize("chargepoint_id, host, port", [(None, "localhost", 1886), (4, "192.168.1.40", 1883)])
def test_local_and_secondary_use_the_same_internal_socket_topics(setup, chargepoint_id, host, port):
    topics, brokers, commands, publisher, cp = setup
    consumer = module.create_consumer(GpioSdm120(id=2, configuration=GpioSdm120Configuration(chargepoint_id)))
    consumer.update()
    assert consumer.store.set.call_args.args[0].power == 500
    assert brokers[-1].host == host
    assert brokers[-1].port == port
    brokers[-1].client.subscribe.assert_called_once_with("openWB/internal_socket/get/#")
    brokers[-1].disconnect.assert_called_once()
    consumer.switch_on()
    commands.assert_any_call("openWB/set/internal_socket/data/set_state", True, hostname=host)
    consumer.switch_off()
    commands.assert_any_call("openWB/set/internal_socket/data/set_state", False, hostname=host)
    assert any(call.args[0] == "openWB/set/internal_socket/data/heartbeat" for call in commands.call_args_list)


def test_measurement_fault_is_transferred_and_off_does_not_clear_it(setup):
    topics, brokers, commands, publisher, cp = setup
    topics.update(fault_state=2, fault_str="SDM120 nicht erreichbar")
    consumer = module.create_consumer(GpioSdm120(id=2))
    consumer.update()
    assert consumer.fault_state.fault_state == 2
    consumer.store.set.assert_not_called()
    consumer.switch_off()
    assert consumer.fault_state.fault_state == 2
    assert consumer.fault_state.fault_str == "SDM120 nicht erreichbar"
    commands.assert_any_call("openWB/set/internal_socket/data/set_state", False, hostname="localhost")
    publisher.pub.assert_any_call("openWB/set/consumer/2/get/fault_state", 2)


def test_warning_and_recovery_are_transferred_to_consumer(setup):
    topics, brokers, commands, publisher, cp = setup
    consumer = module.create_consumer(GpioSdm120(id=2))
    topics.update(fault_state=1, fault_str="Messwarnung")
    consumer.update()
    assert consumer.fault_state.fault_state == 1
    assert consumer.fault_state.fault_str == "Messwarnung"
    topics.update(fault_state=2, fault_str="Messausfall")
    consumer.update()
    assert consumer.fault_state.fault_state == 2
    topics.update(fault_state=0, fault_str="Kein Fehler.")
    consumer.update()
    assert consumer.fault_state.fault_state == 0


def test_complete_fresh_values_do_not_require_retained_no_error_fault_state(setup):
    topics, brokers, commands, publisher, cp = setup
    del topics["fault_state"]
    del topics["fault_str"]
    consumer = module.create_consumer(GpioSdm120(id=2))
    consumer.update()
    assert consumer.fault_state.fault_state == 0
    assert consumer.store.set.call_args.args[0].power == 500


@pytest.mark.parametrize("failure", ["absent", "stale", "incomplete"])
def test_unavailable_measurements_cannot_authorize_on(setup, failure):
    topics, brokers, commands, publisher, cp = setup
    if failure == "absent":
        topics.clear()
    elif failure == "stale":
        topics["timestamp"] -= 16
    else:
        del topics["power"]
    consumer = module.create_consumer(GpioSdm120(id=2))
    consumer.update()
    assert consumer.fault_state.fault_state == 2
    consumer.store.set.assert_not_called()
    consumer.switch_on()
    commands.assert_any_call("openWB/set/internal_socket/data/set_state", False, hostname="localhost")
    assert not any(call.args[1] is True for call in commands.call_args_list)


def test_secondary_ip_is_resolved_for_every_subscription_and_command(setup):
    topics, brokers, commands, publisher, cp = setup
    consumer = module.create_consumer(GpioSdm120(id=2, configuration=GpioSdm120Configuration(4)))
    consumer.update()
    cp.configuration.ip_address = "192.168.1.41"
    consumer.update()
    assert brokers[-1].host == "192.168.1.41"
    consumer.switch_off()
    commands.assert_any_call("openWB/set/internal_socket/data/set_state", False, hostname="192.168.1.41")


def test_connection_failure_does_not_reauthorize_on_using_previous_values(setup, monkeypatch):
    topics, brokers, commands, publisher, cp = setup
    consumer = module.create_consumer(GpioSdm120(id=2))
    consumer.update()
    assert consumer.fault_state.fault_state == 0
    monkeypatch.setattr(module, "BrokerClient", Mock(side_effect=ConnectionError("disconnected")))
    consumer.update()
    consumer.switch_on()
    assert consumer.fault_state.fault_state == 2
    commands.assert_any_call("openWB/set/internal_socket/data/set_state", False, hostname="localhost")
