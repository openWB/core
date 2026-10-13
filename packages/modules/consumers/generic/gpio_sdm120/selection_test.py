from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from helpermodules.subdata import SubData
from modules.consumers.generic.gpio_sdm120.config import GpioSdm120, GpioSdm120Configuration
from modules.consumers.generic.gpio_sdm120.selection import socket_host, validate_selection


@pytest.fixture
def secondary(monkeypatch):
    cp_config = SimpleNamespace(type="external_openwb", configuration=SimpleNamespace(ip_address="192.168.1.40"))
    monkeypatch.setattr(SubData, "cp_data", {"cp4": SimpleNamespace(
        chargepoint=SimpleNamespace(chargepoint_module=SimpleNamespace(config=cp_config)))})
    monkeypatch.setattr(SubData, "consumer_data", {})
    return cp_config


def test_selection_resolves_current_ip_and_rejects_deleted_or_internal_cp(secondary):
    configuration = GpioSdm120Configuration(chargepoint_id=4)
    assert socket_host(configuration) == "192.168.1.40"
    secondary.configuration.ip_address = "192.168.1.41"
    assert socket_host(configuration) == "192.168.1.41"
    secondary.type = "internal_openwb"
    with pytest.raises(ValueError):
        socket_host(configuration)
    with pytest.raises(ValueError):
        socket_host(GpioSdm120Configuration(chargepoint_id=99))


def test_one_consumer_per_physical_box_and_self_is_allowed(secondary, monkeypatch):
    configuration = GpioSdm120Configuration(chargepoint_id=4)
    monkeypatch.setattr(SubData, "consumer_data", {"consumer2": SimpleNamespace(
        num=2, data=SimpleNamespace(module=GpioSdm120(id=2, configuration=configuration)))})
    assert validate_selection(configuration, 2) == "192.168.1.40"
    assert validate_selection(GpioSdm120Configuration()) == "localhost"
    with pytest.raises(ValueError):
        validate_selection(configuration, 3)


def test_changing_assignment_turns_previous_socket_off(secondary, monkeypatch):
    from modules.consumers.generic.gpio_sdm120 import consumer

    old_module = Mock()
    monkeypatch.setattr(SubData, "consumer_data", {"consumer2": SimpleNamespace(
        num=2, module=old_module, data=SimpleNamespace(module=GpioSdm120(id=2)))})
    factory = Mock()
    monkeypatch.setattr(consumer, "ConfigurableConsumer", factory)
    consumer.create_consumer(GpioSdm120(id=2, configuration=GpioSdm120Configuration(chargepoint_id=4)))
    old_module.switch_off.assert_called_once()
    factory.assert_called_once()
